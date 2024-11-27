from typing import Dict, Any, Literal, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

class OperatorResponse(BaseModel):
    """Schema for operator agent's routing decision."""
    intent: Literal["order", "order_query", "fraud", "recommendation", "unknown"]
    confidence: float
    routing: Literal["OrderAgent", "OrderQueryAgent", "FraudAgent", "RecommendationAgent", "FINISH"]
    metadata: Dict[str, Any] = {}

class OperatorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")
        self.intent_prompt = self._setup_prompt()

    def _setup_prompt(self) -> ChatPromptTemplate:
        """Initialize prompts for intent detection."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an intent classification agent. Analyze user messages or prompts and determine the appropriate intent and routing.
            Possible intents are:
            - recommendation: Book recommendations, suggestions, or preferences
            - order: Placing an order or purchasing products
            - order_query: Order tracking, shipping status, order date, etc.
            - fraud: Fraudulent transactions, payment disputes, or damaged products
            - unknown: Unclear intent requiring clarification

            Respond in JSON format:
            {{
                "intent": "<intent>",
                "confidence": <confidence_score>,
                "routing": "<routing>"
            }}

            Examples:
            - User: "Can you recommend some mystery books?" -> {{"intent": "recommendation", "confidence": 0.9, "routing": "RecommendationAgent"}}
            - User: "I want to buy The Great Gatsby" -> {{"intent": "order", "confidence": 0.9, "routing": "OrderAgent"}}
            """),
            ("human", "{input}")
        ])

    async def analyze_intent(self, state: Dict[str, Any]) -> OperatorResponse:
        """Analyze user intent and determine routing."""
        logger.info("=== Starting Intent Analysis ===")
        messages = state.get("messages", [])
        
        if not messages:
            logger.warning("No messages found in state.")
            return self._default_response("No messages found.")

        try:
            # Extract the latest message content
            last_message = messages[-1]
            if isinstance(last_message, HumanMessage):
                original_message = last_message.content.strip()
            else:
                original_message = last_message.get("content", "").strip()

            logger.info(f"Processing message: {original_message}")

            # Validate input
            if not original_message:
                return self._default_response("Empty message content.")

            # Attempt keyword-based routing first
            keyword_decision = self._map_intent_to_routing(original_message)
            if keyword_decision["intent"] != "unknown":
                logger.info(f"Keyword-based intent match: {keyword_decision}")
                return OperatorResponse(**keyword_decision)

            # Use LLM if no keyword match
            logger.info("No keyword match; invoking LLM.")
            response = await self.llm.ainvoke(
                self.intent_prompt.format_messages(input=original_message)
            )

            if isinstance(response, AIMessage):
                llm_raw_response = response.content.strip()
                logger.info(f"Raw LLM response: {llm_raw_response}")

                try:
                    llm_decision = json.loads(llm_raw_response)
                    return OperatorResponse(
                        intent=llm_decision.get("intent", "unknown"),
                        confidence=llm_decision.get("confidence", 0.0),
                        routing=llm_decision.get("routing", "FINISH"),
                        metadata={"method": "llm"}
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid LLM response format: {e}")
                    return self._default_response("Invalid LLM response format.")
            else:
                return self._default_response("Unexpected LLM response type.")
        except Exception as e:
            logger.error(f"Error during intent analysis: {e}")
            return self._default_response(str(e))

    def _map_intent_to_routing(self, message: str) -> Dict[str, Any]:
        """Fallback method to determine intent based on keywords."""
        message_lower = message.lower()
        logger.info(f"Analyzing message for keywords: {message_lower}")

        keywords = {
            "recommendation": [
                "recommend", "suggest", "looking for", "interested in", "like",
                "enjoy", "read", "popular", "favorite", "books"
            ],
            "order": [
                "buy", "purchase", "order", "cart", "checkout", "payment", "price"
            ],
            "order_query": [
                "where", "status", "track", "when", "delivery", "shipped", "arrive"
            ],
            "fraud": [
                "damaged", "wrong", "broken", "missing", "fraud", "refund",
                "complaint", "issue"
            ]
        }

        for intent, words in keywords.items():
            if any(word in message_lower for word in words):
                return {
                    "intent": intent,
                    "confidence": 0.8,
                    "routing": f"{intent.capitalize()}Agent",
                    "metadata": {"method": "keyword"}
                }

        return {
            "intent": "unknown",
            "confidence": 0.5,
            "routing": "FINISH",
            "metadata": {"method": "keyword"}
        }

    def _default_response(self, error: str) -> OperatorResponse:
        """Generate a default response for errors."""
        return OperatorResponse(
            intent="unknown",
            confidence=0.0,
            routing="FINISH",
            metadata={"error": error}
        )
