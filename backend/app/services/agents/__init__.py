from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
import asyncio
import json

from .operator_agent import OperatorAgent
from .order_agent import OrderAgent
from .order_query_agent import OrderQueryAgent
from .fraud_agent import FraudAgent
# from .fraud_agent import FraudAgent

class MultiAgentSystem:
    """
    Coordinates the multi-agent system including:
    - User Proxy Agent (preprocesses input)
    - Operator Agent (determines intent and routes)
    - Specialized Agents (order, tracking, fraud)
    """
    def __init__(self):
        # Initialize agents
        self.operator = OperatorAgent()
        self.order_agent = OrderAgent()
        self.tracking_agent = OrderQueryAgent()
        self.fraud_agent = FraudAgent()
        
        # Setup workflow
        self.setup_graph()

    def setup_graph(self):
        """Configure the agent workflow graph"""
        workflow = StateGraph()
        
        # Add nodes
        workflow.add_node("user_proxy", self.user_proxy.format_for_operator)
        workflow.add_node("operator", self.operator.analyze_intent)
        workflow.add_node("OrderAgent", self.order_agent.process)
        workflow.add_node("OrderQueryAgent", self.tracking_agent.process)
        # workflow.add_node("FraudAgent", self.fraud_agent.process)
        
        # Add edges
        workflow.add_edge("user_proxy", "operator")
        
        # Add conditional edges from operator
        conditional_map = {
            "OrderAgent": "OrderAgent",
            "OrderQueryAgent": "OrderQueryAgent",
            # "FraudAgent": "FraudAgent",
            "FINISH": END
        }
        workflow.add_conditional_edges(
            "operator",
            lambda x: x.routing,
            conditional_map
        )
        
        self.graph = workflow.compile()

    async def process_request(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user request through the multi-agent system
        """
        try:
            # Preprocess input
            processed_input = await self.user_proxy.preprocess_message(user_input)
            if processed_input.get("status") == "error":
                return processed_input

            # Initialize state
            initial_state = {
                "messages": [
                    HumanMessage(content=json.dumps(processed_input))
                ]
            }

            # Process through graph
            async for state in self.graph.astream(initial_state):
                if "__end__" not in state:
                    return {
                        "status": "success",
                        "response": state
                    }

            return {
                "status": "error",
                "message": "Request processing completed without response"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }