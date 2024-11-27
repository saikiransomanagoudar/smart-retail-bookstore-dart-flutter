from typing import Dict, Any, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import logging
import json
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, Graph, START
from langgraph.prebuilt import ToolExecutor

# Import your agents
from backend.app.services.agents.operator_agent import OperatorAgent, OperatorResponse
from backend.app.services.agents.recommendation_agent import RecommendationAgent
from backend.app.services.agents.order_agent import OrderAgent
from backend.app.services.agents.order_query_agent import OrderQueryAgent
from backend.app.services.agents.fraud_agent import FraudAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(), 
        logging.FileHandler('chatbot.log') 
    ]
)
logger = logging.getLogger('ChatbotService')

# Define state schema
class ChatState(TypedDict):
    messages: Sequence[BaseMessage]
    current_agent: str
    metadata: Dict[str, Any] 
    next_step: str
    final_response: Dict[str, Any]

class ChatbotService:
    def __init__(self):
        logger.info("Initializing ChatbotService")
        self.first_interaction = True
        self.greeting_message = "Welcome! I'm BookWorm your personal book assistant. How can I help you today?"

        # Initialize agents
        self.operator = OperatorAgent()
        self.recommendation_agent = RecommendationAgent()
        self.order_agent = OrderAgent()
        self.order_query_agent = OrderQueryAgent()
        self.fraud_agent = FraudAgent()
        
        # Create workflow graph
        self.workflow = self._create_workflow()
        logger.info("ChatbotService initialization complete")

    def _create_workflow(self) -> Graph:
        logger.info("Creating workflow graph")
        workflow = StateGraph(ChatState)

        # Define nodes
        workflow.add_node("route_intent", self._route_intent_step)
        workflow.add_node("recommendation", self._recommendation_step)
        workflow.add_node("order", self._order_step)
        workflow.add_node("order_query", self._order_query_step)
        workflow.add_node("fraud", self._fraud_step)
        workflow.add_node("format_response", self._format_response_step)

        # Define edges
        workflow.add_edge(START, "route_intent")
        
        # Add conditional routing based on operator decision
        workflow.add_conditional_edges(
            "route_intent",
            self._get_next_step,
            {
                "recommendation": "recommendation",
                "order": "order",
                "order_query": "order_query",
                "fraud": "fraud",
                "end": "format_response"
            }
        )

        # All agent nodes route to format_response
        workflow.add_edge("recommendation", "format_response")
        workflow.add_edge("order", "format_response")
        workflow.add_edge("order_query", "format_response")
        workflow.add_edge("fraud", "format_response")

        logger.info("Workflow graph creation complete")
        return workflow.compile()

    def _get_next_step(self, state: ChatState) -> str:
        """Determine next step based on routing decision"""
        logger.info("=== Get Next Step ===")
        
        routing = state["metadata"].get("routing", "FINISH")
        logger.info(f"Current routing value: {routing}")
        
        next_step = "end"
        
        if routing == "RecommendationAgent":
            logger.info("Routing to recommendation step")
            next_step = "recommendation"
        elif routing == "OrderAgent":
            logger.info("Routing to order step")
            next_step = "order"
        elif routing == "OrderQueryAgent":
            logger.info("Routing to order query step")
            next_step = "order_query"
        elif routing == "FraudAgent":
            logger.info("Routing to fraud step")
            next_step = "fraud"
        
        logger.info(f"Determined next step: {next_step}")
        return next_step

    async def _route_intent_step(self, state: ChatState) -> ChatState:
        """Route intent through OperatorAgent"""
        try:
            logging.info("=== Starting Route Intent Step ===")
            logging.info(f"Initial state: {json.dumps(state, default=str)}")
            
            # Send message directly to operator agent
            routing_decision = await self.operator.analyze_intent(state)
            logging.info(f"Routing decision: {routing_decision}")
            
            state["metadata"]["routing"] = routing_decision.routing
            state["metadata"]["intent"] = routing_decision.intent
            state["metadata"]["confidence"] = routing_decision.confidence
            state["current_agent"] = "operator"
            
            logging.info(f"Final route state: {json.dumps(state, default=str)}")
            return state
        except Exception as e:
            logging.error(f"Error in routing: {str(e)}", exc_info=True)
            raise

    async def _recommendation_step(self, state: ChatState) -> ChatState:
        """Process recommendation request"""
        logger.info("Starting recommendation step")
        try:
            response = await self.recommendation_agent.process(state)
            logger.debug(f"Recommendation response: {response}")
            
            state["final_response"] = response
            state["current_agent"] = "recommendation"
            
            logger.info("Recommendation step completed")
            return state
        except Exception as e:
            logger.error(f"Error in recommendation: {str(e)}", exc_info=True)
            raise

    async def _order_step(self, state: ChatState) -> ChatState:
        """Process order request"""
        logger.info("Starting order step")
        try:
            response = await self.order_agent.process(state)
            logger.debug(f"Order response: {response}")
            
            state["final_response"] = response
            state["current_agent"] = "order"
            
            logger.info("Order step completed")
            return state
        except Exception as e:
            logger.error(f"Error in order: {str(e)}", exc_info=True)
            raise

    async def _order_query_step(self, state: ChatState) -> ChatState:
        """Process order query request"""
        logger.info("Starting order query step")
        try:
            response = await self.order_query_agent.process(state)
            logger.debug(f"Order query response: {response}")
            
            state["final_response"] = response
            state["current_agent"] = "order_query"
            
            logger.info("Order query step completed")
            return state
        except Exception as e:
            logger.error(f"Error in order query: {str(e)}", exc_info=True)
            raise

    async def _fraud_step(self, state: ChatState) -> ChatState:
        """Process fraud detection request"""
        logger.info("Starting fraud detection step")
        try:
            response = await self.fraud_agent.process(state)
            logger.debug(f"Fraud detection response: {response}")
            
            state["final_response"] = response
            state["current_agent"] = "fraud"
            
            logger.info("Fraud detection step completed")
            return state
        except Exception as e:
            logger.error(f"Error in fraud detection: {str(e)}", exc_info=True)
            raise

    async def _format_response_step(self, state: ChatState) -> ChatState:
        """Format the final response"""
        logger.info("=== Format Response Step ===")
        logger.info("Starting response formatting step")
        try:
            logger.info(f"Input state to format: {state}")
            if "final_response" not in state:
                logger.warning("No final response found in state")
                state["final_response"] = {
                    "type": "error",
                    "response": "No response generated"
                }
            
            logger.debug(f"Formatted response: {state['final_response']}")
            logger.info("Response formatting complete")
            return state
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}", exc_info=True)
            raise

    async def chat(self, user_input: dict) -> Dict[str, Any]:
        """Process chat input through the workflow"""
        logger.info("Starting new chat interaction")
        try:
            # Handle first interaction
            if self.first_interaction and isinstance(user_input, str):
                self.first_interaction = False
                return {"type": "greeting", "response": self.greeting_message}

            # Create message from input
            message = user_input.get('message', '') if isinstance(user_input, dict) else user_input

            # Initialize state with raw message
            state = ChatState(
                messages=[HumanMessage(content=message)],  # Just pass the raw message
                current_agent="",
                metadata={},
                next_step="",
                final_response={}
            )

            # Run workflow
            final_state = await self.workflow.ainvoke(state)
            return final_state["final_response"]

        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            return {
                "type": "error",
                "response": "I encountered an error processing your request."
            }

chatbot_service = ChatbotService()