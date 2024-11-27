from typing import Dict, Any, Literal, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)

class OperatorResponse(BaseModel):
    """Schema for operator agent's routing decision."""
    intent: Literal["order", "fraud", "recommendation", "unknown"]
    confidence: float
    routing: Literal["OrderAgent", "OrderQueryAgent", "FraudAgent", "RecommendationAgent", "FINISH"]
    metadata: Dict[str, Any] = {}

class OperatorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")
        self.intent_prompt = self._setup_prompt()

    def _setup_prompt(self) -> ChatPromptTemplate:
        """Initialize prompts for intent detection."""
        return ChatPromptTemplate.from_messages([
            ("system", """Determine the user's intents based on the following input: '{input}'.
            Important: Always include "Agent" in routing values.

            Possible intents and routings:
            - For book recommendations:
            intent: "recommendation"
            routing: "RecommendationAgent"
            
            - For placing orders, order status, or order queries:
            intent: "order"
            routing: "OrderAgent"
            
            - For complaints/issues:
            intent: "fraud"
            routing: "FraudAgent"
            
            - For unclear requests:
            intent: "unknown"
            routing: "FINISH"

            Respond in JSON format:
            {{
                "intent": "<intent>",
                "confidence": <confidence_score>,
                "routing": "<routing>",
                "is_intent_switch": <boolean>
            }}"""),
            ("human", """Previous context: {current_context}
            Current message: {input}""")
        ])

    async def analyze_intent(self, state: Dict[str, Any]) -> OperatorResponse:
        """Analyze user intent with better context switching."""
        try:
            messages = state.get("messages", [])
            if not messages:
                return self._create_default_response("No messages found.")

            current_message = messages[-1].content if isinstance(messages[-1], HumanMessage) else messages[-1].get("content", "")
            current_context = state.get("metadata", {}).get("routing", "")

            logger.info(f"Processing message: {current_message}")
            logger.info(f"Current context: {current_context}")

            # Direct mapping for recommendation keywords
            recommendation_keywords = {"recommend", "book", "reading", "suggestion", "like", "interested"}
            if any(keyword in current_message.lower() for keyword in recommendation_keywords):
                return OperatorResponse(
                    intent="recommendation",
                    confidence=0.9,
                    routing="RecommendationAgent",  # Explicitly using correct routing value
                    metadata={"method": "keyword"}
                )

            # Use LLM for other cases
            response = await self.llm.ainvoke(
                self.intent_prompt.format_messages(
                    input=current_message,
                    current_context=current_context
                )
            )

            if isinstance(response, AIMessage):
                llm_decision = json.loads(response.content.strip())
                logger.info(f"LLM decision: {llm_decision}")  # Add this debug log
                
                # Ensure correct routing value format
                routing = llm_decision.get("routing", "FINISH")
                if routing == "recommendation":
                    routing = "RecommendationAgent"
                elif routing == "order":
                    routing = "OrderAgent"
                elif routing == "fraud":
                    routing = "FraudAgent"

                return OperatorResponse(
                    intent=llm_decision.get("intent", "unknown"),
                    confidence=llm_decision.get("confidence", 0.0),
                    routing=routing,
                    metadata={
                        "method": "llm",
                        "is_intent_switch": llm_decision.get("is_intent_switch", False)
                    }
                )

        except Exception as e:
            logger.error(f"Error during intent analysis: {str(e)}")
            return self._create_default_response(str(e))

    def _create_default_response(self, error: str) -> OperatorResponse:
        """Generate a default response for errors."""
        return OperatorResponse(
            intent="recommendation",
            confidence=0.7,
            routing="RecommendationAgent",  # Always use correct routing value
            metadata={"error": error}
        )

    def _map_intent_to_routing(self, message: str) -> Dict[str, Any]:
        """Map intent to correct routing value."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["recommend", "book", "reading"]):
            return {
                "intent": "recommendation",
                "confidence": 0.8,
                "routing": "RecommendationAgent",  # Correct routing value
                "metadata": {"method": "keyword"}
            }
        
        return {
            "intent": "unknown",
            "confidence": 0.5,
            "routing": "FINISH",
            "metadata": {"method": "keyword"}
        }