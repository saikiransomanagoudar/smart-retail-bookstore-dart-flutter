from typing import Dict, Any, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import logging
import json
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, Graph, START
from langgraph.prebuilt import ToolExecutor

# Import your agents
from backend.app.services.agents.operator_agent import OperatorAgent, OperatorResponse
from backend.app.services.agents.recommendation_agent import RecommendationAgent
from backend.app.services.agents.order_agent import OrderAgent
# from backend.app.services.agents.order_query_agent import OrderQueryAgent
from backend.app.services.agents.fraud_agent import FraudAgent
from backend.app.models.orders import Order

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
        
        # Add conversation state tracking
        self.active_sessions = {}  # Store active conversation contexts

        # Initialize agents
        self.operator = OperatorAgent()
        self.recommendation_agent = RecommendationAgent()
        self.order_agent = OrderAgent()
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
        # workflow.add_node("order_query", self._order_query_step)
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
                # "order_query": "order_query",
                "fraud": "fraud",
                "end": "format_response"
            }
        )

        # All agent nodes route to format_response
        workflow.add_edge("recommendation", "format_response")
        workflow.add_edge("order", "format_response")
        # workflow.add_edge("order_query", "format_response")
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
        # elif routing == "OrderQueryAgent":
        #     logger.info("Routing to order query step")
        #     next_step = "order_query"
        elif routing == "FraudAgent":
            logger.info("Routing to fraud step")
            next_step = "fraud"
        
        logger.info(f"Determined next step: {next_step}")
        return next_step

    async def _route_intent_step(self, state: ChatState) -> ChatState:
        """Route intent through OperatorAgent"""
        try:
            logging.info("=== Starting Route Intent Step ===")

            if state['metadata'].get('current_agent') == 'fraud':
                state['metadata']['routing'] = 'FraudAgent'
                return state

            # Otherwise, get routing from operator
            routing_decision = await self.operator.analyze_intent(state)
            logging.info(f"Routing decision: {routing_decision}")
            
            state["metadata"]["routing"] = routing_decision.routing
            state["metadata"]["intent"] = routing_decision.intent
            state["metadata"]["confidence"] = routing_decision.confidence
            state["current_agent"] = "operator"
            
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
            # Get user_id from metadata if available
            user_id = state.get("metadata", {}).get("user_id")
            messages = state.get("messages", [])
            last_message = messages[-1].content if messages else ""
            
            logger.info(f"Processing order with user_id: {user_id}")
            logger.info(f"Message content: {last_message}")

            # Handle order queries directly without LLM
            if any(keyword in last_message.lower() for keyword in ["orders", "my orders", "show orders", "order history"]):
                orders = Order.get_user_orders(user_id)
                if orders:
                    logger.info(f"Found orders for user: {orders}")
                    state["final_response"] = {
                        "type": "order_response",
                        "response": {
                            "message": "Here are your orders:",
                            "order_details": orders
                        }
                    }
                else:
                    logger.info("No orders found for user")
                    state["final_response"] = {
                        "type": "error",
                        "response": "No orders found for your account."
                    }

            # Handle specific order queries
            elif "order" in last_message.lower() and any(char.isdigit() for char in last_message):
                import re
                match = re.search(r'ORD-\d+', last_message)
                if match:
                    order_id = match.group()
                    logger.info(f"Searching for specific order: {order_id}")
                    order_details = Order.get_order_details(order_id, user_id)
                    if order_details:
                        logger.info(f"Found order details: {order_details}")
                        state["final_response"] = {
                            "type": "order_response",
                            "response": {
                                "message": "Here is your order:",
                                "order_details": {
                                    "order_id": order_details["order_id"],
                                    "title": order_details["title"],
                                    "price": order_details["price"],
                                    "total_quantity": order_details["total_quantity"],
                                    "purchase_date": order_details["purchase_date"],
                                    "expected_delivery": order_details["expected_delivery"]
                                }
                            }
                        }
                    else:
                        logger.info(f"Order not found: {order_id}")
                        state["final_response"] = {
                            "type": "error",
                            "response": f"Order {order_id} not found."
                        }
            else:
                # For general queries, use the order agent
                response = await self.order_agent.process(state)
                state["final_response"] = response

            state["current_agent"] = "order"
            logger.info("Order step completed")
            return state
            
        except Exception as e:
            logger.error(f"Error in order step: {str(e)}", exc_info=True)
            state["final_response"] = {
                "type": "error",
                "response": "An error occurred while processing your order request."
            }
            return state

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
            # Extract user ID for session management
            user_id = user_input.get('metadata', {}).get('user_id')
            
            # Handle first interaction
            if self.first_interaction and isinstance(user_input, str):
                self.first_interaction = False
                return {"type": "greeting", "response": self.greeting_message}

            # Get or create session state
            session = self.active_sessions.get(user_id, {
                'current_agent': None,
                'conversation_state': None,
                'messages': []
            })

            # Extract message and metadata
            message = user_input.get('message', '') if isinstance(user_input, dict) else user_input
            metadata = user_input.get('metadata', {})

            # Update metadata with session context
            metadata.update({
                'current_agent': session['current_agent'],
                'conversation_state': session['conversation_state']
            })

            # Initialize state with message and metadata
            state = ChatState(
                messages=[*session['messages'], HumanMessage(content=message)],
                current_agent=session['current_agent'] or "",
                metadata=metadata,
                next_step="",
                final_response={}
            )

            # If we're in the middle of a fraud flow, bypass operator
            if session['current_agent'] == 'fraud':
                state['metadata']['routing'] = 'FraudAgent'
                final_state = await self.workflow.ainvoke(state)
            else:
                # Run normal workflow
                final_state = await self.workflow.ainvoke(state)

            # Update session state
            self.active_sessions[user_id] = {
                'current_agent': final_state['current_agent'],
                'conversation_state': final_state['metadata'].get('conversation_state'),
                'messages': [*session['messages'], HumanMessage(content=message)]
            }

            return final_state["final_response"]

        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            return {
                "type": "error",
                "response": "I encountered an error processing your request."
            }
        
    async def place_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process order placement through OrderAgent"""
        logger.info("Processing order placement")
        try:
            # Create a state object for the order agent
            state = ChatState(
                messages=[HumanMessage(content=json.dumps(data))],
                current_agent="order",
                metadata={
                    "routing": "OrderAgent",
                    "intent": "order",
                    "confidence": 1.0
                },
                next_step="",
                final_response={}
            )

            # Process the order through the order agent
            response = await self.order_agent.process(state)
            
            if response["type"] == "order_processing":
                # Order validation successful, proceed with placement
                order_data = response["response"]["data"]
                validation_result = self.order_agent._validate_order_data(order_data)
                
                if validation_result["is_valid"]:
                    # Generate order confirmation details
                    order_confirmation = {
                        "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "total_cost": sum(item["price"] * item["quantity"] for item in order_data["order_data"]),
                        "order_placed_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "expected_delivery": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                        "status": "confirmed",
                        "items": order_data["order_data"]
                    }
                    
                    return {
                        "type": "order_confirmation",
                        "response": {
                            "message": "Order placed successfully!",
                            "order_details": order_confirmation
                        }
                    }
                else:
                    return {
                        "type": "error",
                        "response": f"Order validation failed: {validation_result['error']}"
                    }
            
            return response

        except Exception as e:
            logger.error(f"Error processing order: {str(e)}")
            return {
                "type": "error",
                "response": "An error occurred while processing your order. Please try again."
            }

chatbot_service = ChatbotService()