BaseModelfrom typing import Dict, Any, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import json

class OperatorResponse(BaseModel):
    """Schema for operator agent's routing decision"""
    intent: Literal["order", "tracking", "fraud", "unknown"]
    confidence: float
    routing: Literal["OrderAgent", "TrackingAgent", "FraudAgent", "FINISH"]
    metadata: Dict[str, Any] = {}

class OperatorAgent:
    """
    Analyzes user intent and routes to appropriate agent
    Acts as the supervisor for the multi-agent system
    """
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")
        self.setup_prompts()

    def setup_prompts(self):
        """Initialize prompts for intent detection"""
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intent classification agent. Analyze user messages and determine the appropriate routing.
            Possible intents are:
            1. order: New order placement or order-related queries
            2. tracking: Order tracking, shipping status, or damaged delivery claims
            3. fraud: Fraudulent transactions or payment disputes
            4. unknown: Unclear intent requiring clarification

            For each message, determine:
            - Primary intent
            - Confidence score (0.0 to 1.0)
            - Appropriate routing (OrderAgent, TrackingAgent, FraudAgent, or FINISH)
            
            Consider:
            - Message content
            - Presence of images/receipts
            - Order IDs or other metadata"""),
            ("human", "{input}"),
        ])

    async def analyze_intent(self, state: Dict[str, Any]) -> OperatorResponse:
        """Analyze user intent and determine routing"""
        try:
            # Extract message content from state
            messages = state.get("messages", [])
            if not messages:
                return OperatorResponse(
                    intent="unknown",
                    confidence=0.0,
                    routing="FINISH",
                    metadata={"error": "No messages found"}
                )

            # Parse the message content
            message_data = json.loads(messages[-1].content)
            
            # Create context for intent analysis
            analysis_context = {
                "message": message_data.get("original_message"),
                "type": message_data.get("type"),
                "metadata": message_data.get("metadata", {})
            }

            # Use LLM to detect intent
            response = await self.llm.ainvoke(
                self.intent_prompt.format_messages(input=json.dumps(analysis_context))
            )

            # Parse LLM response and map to routing decision
            routing_decision = self._map_intent_to_routing(response.content)
            
            return OperatorResponse(**routing_decision)

        except Exception as e:
            print(f"Error in intent analysis: {str(e)}")
            return OperatorResponse(
                intent="unknown",
                confidence=0.0,
                routing="FINISH",
                metadata={"error": str(e)}
            )

    def _map_intent_to_routing(self, llm_response: str) -> Dict[str, Any]:
        """Map LLM response to routing decision"""
        # Add your logic to parse LLM response and map to routing decision
        # This is a simplified example
        if "order" in llm_response.lower():
            return {
                "intent": "order",
                "confidence": 0.9,
                "routing": "OrderAgent"
            }
        elif "track" in llm_response.lower() or "damage" in llm_response.lower():
            return {
                "intent": "tracking",
                "confidence": 0.9,
                "routing": "TrackingAgent"
            }
        elif "fraud" in llm_response.lower() or "dispute" in llm_response.lower():
            return {
                "intent": "fraud",
                "confidence": 0.9,
                "routing": "FraudAgent"
            }
        else:
            return {
                "intent": "unknown",
                "confidence": 0.5,
                "routing": "FINISH"
            }

    def format_for_agent(self, state: Dict[str, Any], routing_decision: OperatorResponse) -> Dict[str, Any]:
        """Format the state for the target agent"""
        messages = state.get("messages", [])
        if not messages:
            return state

        try:
            message_data = json.loads(messages[-1].content)
            return {
                "messages": messages,
                "metadata": {
                    **message_data.get("metadata", {}),
                    "intent": routing_decision.intent,
                    "confidence": routing_decision.confidence
                }
            }
        except:
            return state