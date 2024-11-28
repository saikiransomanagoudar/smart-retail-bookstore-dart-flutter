from typing import Dict, Any, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
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

    async def _analyze_damage(self, image_data: str, message: str) -> Dict[str, Any]:
        """Analyze damage from image and message"""
        try:
            # Create analysis prompt with image and message
            analysis = await self.damage_llm.ainvoke(
                self.damage_prompt.format_messages(
                    image_description=message,
                    context={"image": image_data}
                )
            )

            result = json.loads(analysis.content)
            
            # Create decision based on analysis
            decision = {
                "case_id": f"DMG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "damage_type": result.get("damage_type", "shipping damage"),
                "severity": result.get("severity", "medium"),
                "likely_impact": result.get("likely_impact", "potential product damage"),
                "recommended_action": result.get("recommended_action", "replace"),
                "confidence": result.get("confidence", 0.8),
                "reason": result.get("reason", "Based on visible shipping damage")
            }

            return decision

        except Exception as e:
            logger.error(f"Error in damage analysis: {str(e)}")
            return {
                "case_id": f"DMG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "damage_type": "shipping damage",
                "severity": "under review",
                "recommended_action": "replace",
                "confidence": 0.7,
                "reason": "Default assessment due to analysis error"
            }

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process fraud or damage claims"""
        try:
            messages = state.get("messages", [])
            if not messages:
                return self._create_error_response("No message found to process")

            # Extract the latest message
            try:
                last_message = messages[-1].content
                if isinstance(last_message, str) and last_message.startswith('{"type"'):
                    message_data = json.loads(last_message)
                    current_message = message_data.get("content", "")
                    # Check for image in latest message
                    if message_data.get("metadata", {}).get("image"):
                        image_data = message_data["metadata"]["image"]
                    else:
                        image_data = None
                else:
                    current_message = last_message
                    image_data = None
            except json.JSONDecodeError:
                current_message = last_message
                image_data = None

            # If we have an image, process the damage analysis
            if image_data:
                try:
                    analysis = await self._analyze_damage(image_data, current_message)
                    return {
                        "type": "damage_assessment",
                        "response": {
                            "message": f"""Thank you for reporting the damaged delivery. Here's my assessment:

    Damage Type: {analysis['damage_type']}
    Severity: {analysis['severity']}
    Action: {analysis['recommended_action'].title()}

    Next Steps:
    1. We'll process a {analysis['recommended_action']} for your order
    2. You'll receive a confirmation email within 24 hours
    3. Please keep the damaged packaging for potential review

    Your case reference: {analysis['case_id']}

    Is there anything else you need assistance with?""",
                            "assessment": analysis
                        }
                    }
                except Exception as e:
                    logger.error(f"Error analyzing damage: {str(e)}")
                    return self._create_error_response("Error analyzing damage. Please try again.")

            # Handle fraud report without image
            if "fraud" in current_message.lower():
                return {
                    "type": "clarification",
                    "response": {
                        "message": """Could you provide more details about the fraudulent activity? Please include:
    1. Transaction details
    2. Date of the incident
    3. Any relevant documentation or screenshots"""
                    }
                }

            # Handle damage report without image
            if any(word in current_message.lower() for word in ["damage", "damaged", "broken"]):
                return {
                    "type": "clarification",
                    "response": {
                        "message": """I can help you with your damage report. Please:
    1. Upload a photo of the damaged item/packaging
    2. Provide the date you received the delivery
    3. Mention if the damage is to the packaging, product, or both"""
                    }
                }

            # Default response
            return {
                "type": "clarification",
                "response": {
                    "message": "Could you please provide more details about your issue? Are you reporting fraud or product damage?"
                }
            }

        except Exception as e:
            logger.error(f"Error in fraud processing: {str(e)}")
            return self._create_error_response(str(e))

    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Create formatted error response"""
        return {
            "type": "error",
            "response": {
                "message": "I apologize, but I'm having trouble processing your request. Could you please provide more details about the fraud or damage you're reporting?",
                "error": str(error)
            }
        }

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
            # Extract OCR text from image if present
            image_data = message_data.get("metadata", {}).get("image", "")
            conversation_history = message_data.get("metadata", {}).get("conversation_history", [])
            
            # Perform OCR if image is present
            ocr_text = self._perform_ocr(image_data) if image_data else ""
            
            # Combine all available information for analysis
            analysis_text = f"""
            User Report: {message_data.get('content', '')}
            Conversation History: {json.dumps(conversation_history)}
            Transaction Details (OCR): {ocr_text}
            """

            # Analyze with fraud detection LLM
            analysis = await self.fraud_llm.ainvoke(
                self.fraud_prompt.format_messages(
                    transaction_details=analysis_text
                )
            )

            result = json.loads(analysis.content)
            
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