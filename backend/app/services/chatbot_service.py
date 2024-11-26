from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
import logging
import json
from langchain_core.prompts import ChatPromptTemplate

class ChatbotService:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")
        self.memory = ConversationBufferMemory(return_messages=True)
        self.first_interaction = True
        self.greeting_message = "Welcome! I'm BookWorm your personal book assistant. How can I help you today?"
        self.setup_prompts()

    def setup_prompts(self):
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are BookWorm, a personal book assistant. You help customers with:
            1. Placing new orders
            2. Checking order status
            3. Book recommendations
            4. General inquiries about books

            When discussing orders:
            - For new orders: Ask about book preferences and guide through ordering process
            - For order status: Ask for order ID or help find their order
            - For order history: Guide them to view their past orders

            Keep responses friendly, clear, and focused on books and orders."""),
            ("human", "{input}")
        ])

    async def chat(self, user_input: dict):
        try:
            logging.info(f"Received user input: {user_input}")
            
            # Handle first interaction
            if self.first_interaction and isinstance(user_input, str):
                self.first_interaction = False
                return {"type": "greeting", "response": self.greeting_message}

            # Process message content
            if isinstance(user_input, dict):
                message = user_input.get('message', '')
            else:
                message = user_input

            # Clear conversation if requested
            if isinstance(message, str) and message.lower() == "clear":
                self.reset_state()
                return {"type": "system", "response": "How can I help you with books today?"}

            # Handle basic greetings
            if isinstance(message, str) and message.lower() in ["hi", "hello"]:
                self.first_interaction = False
                return {
                    "type": "greeting",
                    "response": self.greeting_message
                }

            try:
                # Determine intent and response type
                response_type = "general"
                if isinstance(message, str):
                    message_lower = message.lower()
                    if "new order" in message_lower or "place order" in message_lower:
                        response_type = "order"
                        chain = ChatPromptTemplate.from_messages([
                            ("system", "You are helping a customer place a new order. Guide them through the process and ask for necessary details."),
                            ("human", "{input}")
                        ]) | self.llm
                    elif "order" in message_lower and any(word in message_lower for word in ["status", "track", "find", "history"]):
                        response_type = "order_query"
                        chain = ChatPromptTemplate.from_messages([
                            ("system", "You are helping a customer find order information. Ask for order ID if needed."),
                            ("human", "{input}")
                        ]) | self.llm
                    else:
                        chain = self.chat_prompt | self.llm

                # Get response from LLM
                response = await chain.ainvoke({"input": message})
                
                # Extract response content
                response_content = response.content if isinstance(response, AIMessage) else str(response)
                logging.info(f"LLM Response: {response_content}")

                # Store conversation in memory
                self.memory.chat_memory.add_user_message(message)
                self.memory.chat_memory.add_ai_message(response_content)

                return {
                    "type": response_type,
                    "response": response_content
                }

            except Exception as e:
                logging.error(f"Error getting LLM response: {str(e)}")
                return {
                    "type": "error",
                    "response": "I'm having trouble understanding that. Could you please rephrase your request?"
                }

        except Exception as e:
            logging.error(f"Error in chat processing: {str(e)}")
            return {
                "type": "error",
                "response": "I encountered an error processing your request. Please try again."
            }

    def reset_state(self):
        """Reset the conversation state"""
        self.first_interaction = True
        self.memory.clear()

    async def process_order_request(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Process order-related requests"""
        try:
            # Create order-specific prompt
            order_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are BookWorm, handling order-related requests. 
                For new orders: Guide the customer through order placement.
                For order status: Ask for order ID or help locate their order.
                For order history: Help them view their past orders."""),
                ("human", "User ID: {user_id}\nRequest: {input}")
            ])

            chain = order_prompt | self.llm
            response = await chain.ainvoke({
                "input": user_input,
                "user_id": user_id
            })

            # Extract response content
            response_content = response.content if isinstance(response, AIMessage) else str(response)
            
            return {
                "type": "order_query",
                "response": response_content
            }
        except Exception as e:
            logging.error(f"Error processing order request: {str(e)}")
            return {
                "type": "error",
                "response": "I'm having trouble with your order request. Could you please try again?"
            }

chatbot_service = ChatbotService()