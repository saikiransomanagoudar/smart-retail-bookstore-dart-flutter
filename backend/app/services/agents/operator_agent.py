from typing import Dict, Any, Literal, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import json
import logging
import random

logger = logging.getLogger(__name__)

class OperatorResponse(BaseModel):
    """Schema for operator agent's routing decision."""
    intent: Literal["order", "fraud", "recommendation", "greeting", "unknown"]  # Added greeting
    confidence: float
    routing: Literal["OrderAgent", "FraudAgent", "RecommendationAgent", "FINISH"]
    metadata: Dict[str, Any] = {}

class OperatorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")
        self.intent_prompt = self._setup_prompt()
        
        # Add greeting templates
        self.greetings = {
            "initial": [
                "Welcome! I'm BookWorm, your personal book assistant. I can help you find books, track orders, report damaged shipments, or handle any concerns about book purchases. How can I assist you today?",
                "Hi there! I'm BookWorm. Whether you need book recommendations, want to check an order, or need to report a damaged delivery, I'm here to help. What can I do for you?",
                "Hello! I'm your BookWorm assistant. I can help you with finding your next great read, checking order status, reporting damaged deliveries, or handling any transaction concerns. What would you like to explore?"
            ],
            "follow_up": [
                "How can I help with your book-related needs today? I can assist with recommendations, orders, or any issues you're experiencing.",
                "What can I help you with? Whether it's finding books, checking orders, or reporting issues, I'm here to assist.",
                "Need help finding a book, checking an order, or reporting a problem? I'm here to help!"
            ]
        }

    def _setup_prompt(self) -> ChatPromptTemplate:
        """Initialize prompts for intent detection."""
        return ChatPromptTemplate.from_messages([
            ("system", """Determine the user's intents based on the following input: '{input}'.
            Important: Always include "Agent" in routing values.

            Possible intents and routings:
            - For greetings:
            intent: "greeting"
            routing: "RecommendationAgent"
            
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
            routing: "RecommendationAgent"

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

            # Parse message content
            try:
                raw_message = messages[-1].content if isinstance(messages[-1], HumanMessage) else messages[-1].get("content", "")
                if isinstance(raw_message, str) and raw_message.startswith('{"type"'):
                    message_data = json.loads(raw_message)
                    current_message = message_data.get("content", "")
                else:
                    current_message = raw_message
            except json.JSONDecodeError:
                current_message = raw_message

            metadata = state.get("metadata", {})
            current_context = metadata.get("routing", "")
            has_image = metadata.get("image") is not None
            current_agent = metadata.get("current_agent", "")

            logger.info(f"Processing message: {current_message}")
            logger.info(f"Current context: {current_context}")
            logger.info(f"Current agent: {current_agent}")
            logger.info(f"Has image: {has_image}")

            message_lower = str(current_message).lower().strip()

            # Handle greetings (only if not in another context)
            message_lower = current_message.lower().strip()
            is_greeting = message_lower in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
            
            if is_greeting and not current_context:
                is_initial = len(messages) <= 1
                greeting = random.choice(self.greetings["initial"] if is_initial else self.greetings["follow_up"])
                
                return OperatorResponse(
                    intent="greeting",
                    confidence=0.95,
                    routing="RecommendationAgent",
                    metadata={
                        "method": "greeting",
                        "response": greeting
                    }
                )

            # Use keyword matching first
            intent_routing = self._map_intent_to_routing(message_lower)
            if intent_routing.get("confidence", 0) > 0.7:
                return OperatorResponse(**intent_routing)

            # Check for explicit intent to switch context
            order_keywords = {"order history", "orders", "my orders", "show orders", "order status"}
            if any(keyword in message_lower for keyword in order_keywords):
                logger.info("Switching to OrderAgent for order history")
                return OperatorResponse(
                    intent="order",
                    confidence=0.95,
                    routing="OrderAgent",
                    metadata={
                        "method": "keyword",
                        "context_switch": True,
                        "previous_context": current_context
                    }
                )

            # Check for new image uploads
            if has_image:
                logger.info("New image detected - maintaining/switching to FraudAgent")
                return OperatorResponse(
                    intent="fraud",
                    confidence=0.95,
                    routing="FraudAgent",
                    metadata={
                        "method": "image_detection",
                        "has_image": True
                    }
                )

            # Check for fraud/damage keywords
            fraud_keywords = {"fraud", "damaged", "damage", "broken", "complaint"}
            if any(keyword in message_lower for keyword in fraud_keywords):
                logger.info("Detected fraud/damage keywords")
                return OperatorResponse(
                    intent="fraud",
                    confidence=0.95,
                    routing="FraudAgent",
                    metadata={
                        "method": "keyword"
                    }
                )

            # Check for recommendation keywords
            recommendation_keywords = {"recommend", "book", "reading", "suggestion", "like", "interested"}
            if any(keyword in message_lower for keyword in recommendation_keywords):
                logger.info("Switching to RecommendationAgent")
                return OperatorResponse(
                    intent="recommendation",
                    confidence=0.9,
                    routing="RecommendationAgent",
                    metadata={
                        "method": "keyword",
                        "context_switch": True
                    }
                )

            # If no specific keywords are found and we're in fraud context,
            # only maintain context if the message is relevant
            if current_context == "FraudAgent" and not any(word in message_lower for word in 
            ["yes", "no", "ok", "thanks", "help", "support", "issue", "problem", "case"]):
                logger.info("Allowing context switch from fraud agent")
                response = await self.llm.ainvoke(
                    self.intent_prompt.format_messages(
                        input=current_message,
                        current_context=current_context
                    )
                )
            
            if isinstance(response, AIMessage):
                llm_decision = json.loads(response.content.strip())
                logger.info(f"LLM decision for context switch: {llm_decision}")
                
                routing = llm_decision.get("routing", "RecommendationAgent")
                if routing not in ["RecommendationAgent", "OrderAgent", "FraudAgent"]:
                    routing = "RecommendationAgent"

                # Reset context to the new agent
                return OperatorResponse(
                    intent=llm_decision.get("intent", "unknown"),
                    confidence=llm_decision.get("confidence", 0.0),
                    routing=routing,
                    metadata={
                        "method": "llm",
                        "context_switch": True
                    }
                )


            # Maintain current context if no clear intent to switch
            return OperatorResponse(
                intent=current_agent or "unknown",
                confidence=0.7,
                routing=current_context or "RecommendationAgent",
                metadata={
                    "method": "context_maintenance"
                }
            )

        except Exception as e:
            logger.error(f"Error during intent analysis: {str(e)}")
            return self._create_default_response(str(e))

    def _create_default_response(self, error: str) -> OperatorResponse:
        """Generate a default response for errors."""
        return OperatorResponse(
            intent="greeting",
            confidence=0.7,
            routing="RecommendationAgent",
            metadata={
                "error": error,
                "response": "I'd be happy to help you with books, orders, or any issues. What would you like to know?"
            }
        )

    def _map_intent_to_routing(self, message: str) -> Dict[str, Any]:
        """Map intent to correct routing value."""
        # Order keywords
        order_keywords = {"order", "purchase", "buy", "cart", "checkout", "shipping", "delivery", "track", "status"}
        if any(word in message for word in order_keywords):
            return {
                "intent": "order",
                "confidence": 0.8,
                "routing": "OrderAgent",
                "metadata": {"method": "keyword"}
            }

        # Fraud/damage keywords
        fraud_keywords = {"fraud", "damaged", "damage", "broken", "issue", "problem", "wrong", "complaint"}
        if any(word in message for word in fraud_keywords):
            return {
                "intent": "fraud",
                "confidence": 0.8,
                "routing": "FraudAgent",
                "metadata": {"method": "keyword"}
            }

        # Recommendation keywords
        recommendation_keywords = {"recommend", "book", "reading", "suggestion", "like", "interested"}
        if any(word in message for word in recommendation_keywords):
            return {
                "intent": "recommendation",
                "confidence": 0.8,
                "routing": "RecommendationAgent",
                "metadata": {"method": "keyword"}
            }

        # Default case
        return {
            "intent": "unknown",
            "confidence": 0.5,
            "routing": "RecommendationAgent",
            "metadata": {"method": "default"}
        }