from typing import Dict, Any, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json
import logging
from pydantic import BaseModel
import base64
from PIL import Image
import io
import pytesseract
from datetime import datetime

class FraudDecision(BaseModel):
    """Schema for fraud/damage decision"""
    decision: Literal["refund", "replace", "decline", "escalate"]
    confidence: float
    reason: str
    case_id: str
    metadata: Dict[str, Any] = {}

class FraudAgent:
    """Handles fraud claims and damaged shipment reports"""
    
    def __init__(self):
        # Initialize LLMs with different temperatures for different tasks
        self.damage_llm = ChatOpenAI(temperature=0.3, model="gpt-4-vision-preview")
        self.fraud_llm = ChatOpenAI(temperature=0.2, model="gpt-4o-mini")
        self.setup_prompts()

    def setup_prompts(self):
        """Initialize prompts for different scenarios"""
        self.damage_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a damage assessment expert. Analyze shipping box images to:
            1. Identify type and severity of damage
            2. Assess impact on contained items
            3. Determine appropriate action (refund, replace, or escalate)
            
            Consider:
            - Damage type (crushing, water, tearing)
            - Damage location and extent
            - Likelihood of product damage
            
            Return your analysis in JSON format with:
            {
                "damage_type": string,
                "severity": "low"|"medium"|"high",
                "likely_impact": string,
                "recommended_action": "refund"|"replace"|"escalate",
                "confidence": float,
                "reason": string
            }"""),
            ("human", "{image_description}\n{context}")
        ])

        self.fraud_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a fraud detection expert. Analyze transaction details to:
            1. Identify suspicious patterns
            2. Verify transaction legitimacy
            3. Determine appropriate action (refund, decline, or escalate)
            
            Consider:
            - Transaction location and time
            - Amount patterns
            - Merchant information
            - Customer history
            
            Return your analysis in JSON format with:
            {
                "fraud_indicators": [string],
                "risk_level": "low"|"medium"|"high",
                "recommended_action": "refund"|"decline"|"escalate",
                "confidence": float,
                "reason": string
            }"""),
            ("human", "{transaction_details}")
        ])

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process fraud or damage claims"""
        try:
            messages = state.get("messages", [])
            if not messages:
                return self._create_error_response("No message found to process")

            message_data = json.loads(messages[-1].content)
            message_type = message_data.get("type", "")
            
            if message_type == "image" and "image" in message_data.get("metadata", {}):
                # Handle damage assessment with image
                return await self._handle_damage_claim(message_data)
            elif "fraud" in message_data.get("original_message", "").lower():
                # Handle fraud claim with OCR
                return await self._handle_fraud_claim(message_data)
            else:
                return self._create_error_response("Invalid request type")

        except Exception as e:
            logging.error(f"Error in fraud/damage processing: {str(e)}")
            return self._create_error_response(str(e))

    async def _handle_damage_claim(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process damaged shipment claims"""
        try:
            # Extract image and analyze damage
            image_data = message_data.get("metadata", {}).get("image", "")
            original_message = message_data.get("original_message", "")

            # Analyze image with Vision model
            analysis = await self.damage_llm.ainvoke(
                self.damage_prompt.format_messages(
                    image_description=original_message,
                    context={"image": image_data}
                )
            )

            try:
                result = json.loads(analysis.content)
            except json.JSONDecodeError:
                return self._create_error_response("Error parsing damage analysis")

            # Create decision based on analysis
            decision = FraudDecision(
                decision="refund" if result["recommended_action"] == "refund"
                    else "replace" if result["recommended_action"] == "replace"
                    else "escalate",
                confidence=result["confidence"],
                reason=result["reason"],
                case_id=f"DMG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                metadata={
                    "damage_type": result["damage_type"],
                    "severity": result["severity"],
                    "likely_impact": result["likely_impact"]
                }
            )

            return {
                "type": "damage_assessment",
                "response": {
                    "decision": decision.decision,
                    "reason": decision.reason,
                    "case_id": decision.case_id,
                    "next_steps": self._get_next_steps(decision.decision),
                    "metadata": decision.metadata
                }
            }

        except Exception as e:
            logging.error(f"Error in damage assessment: {str(e)}")
            return self._create_error_response("Error processing damage claim")

    async def _handle_fraud_claim(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process fraudulent transaction claims"""
        try:
            # Extract OCR image if present
            image_data = message_data.get("metadata", {}).get("image", "")
            original_message = message_data.get("original_message", "")

            # Perform OCR if image is present
            transaction_details = ""
            if image_data:
                transaction_details = self._perform_ocr(image_data)
            
            # Combine OCR results with user message
            analysis_text = f"{original_message}\n\nTransaction Details:\n{transaction_details}"

            # Analyze with fraud detection LLM
            analysis = await self.fraud_llm.ainvoke(
                self.fraud_prompt.format_messages(
                    transaction_details=analysis_text
                )
            )

            try:
                result = json.loads(analysis.content)
            except json.JSONDecodeError:
                return self._create_error_response("Error parsing fraud analysis")

            # Create decision based on analysis
            decision = FraudDecision(
                decision="refund" if result["recommended_action"] == "refund"
                    else "decline" if result["recommended_action"] == "decline"
                    else "escalate",
                confidence=result["confidence"],
                reason=result["reason"],
                case_id=f"FRD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                metadata={
                    "fraud_indicators": result["fraud_indicators"],
                    "risk_level": result["risk_level"]
                }
            )

            return {
                "type": "fraud_assessment",
                "response": {
                    "decision": decision.decision,
                    "reason": decision.reason,
                    "case_id": decision.case_id,
                    "next_steps": self._get_next_steps(decision.decision),
                    "metadata": decision.metadata
                }
            }

        except Exception as e:
            logging.error(f"Error in fraud assessment: {str(e)}")
            return self._create_error_response("Error processing fraud claim")

    def _perform_ocr(self, image_data: str) -> str:
        """Extract text from image using OCR"""
        try:
            # Remove data URL prefix if present
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]

            # Convert base64 to image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Perform OCR
            text = pytesseract.image_to_string(image)
            return text.strip()

        except Exception as e:
            logging.error(f"Error in OCR processing: {str(e)}")
            return ""

    def _get_next_steps(self, decision: str) -> str:
        """Get next steps based on decision"""
        steps = {
            "refund": """Next steps:
1. Your refund will be processed within 3-5 business days
2. You'll receive a confirmation email with refund details
3. Keep the damaged item/documentation for possible review""",
            
            "replace": """Next steps:
1. A replacement will be shipped within 2 business days
2. You'll receive tracking information via email
3. Use the provided return label to send back the damaged item""",
            
            "escalate": """Next steps:
1. Your case has been escalated to our specialist team
2. A representative will contact you within 24 hours
3. Please have any relevant documentation ready""",
            
            "decline": """Next steps:
1. Review the detailed explanation provided
2. If you disagree, you can appeal with additional documentation
3. Contact your bank for more information about the transaction"""
        }
        return steps.get(decision, "Our team will contact you with next steps.")

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create formatted error response"""
        return {
            "type": "error",
            "response": {
                "message": error_message,
                "case_id": f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        }