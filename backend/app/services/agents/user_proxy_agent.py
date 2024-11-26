from typing import Dict, Any
from langchain_core.messages import HumanMessage
import json
import base64

class UserProxyAgent:
    """
    Preprocesses user input and formats it for the operator agent.
    Acts as the first point of contact for all incoming requests.
    """
    def __init__(self):
        self.supported_image_formats = ['image/jpeg', 'image/png']
        
    async def preprocess_message(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate incoming user messages
        Returns formatted message for operator agent
        """
        try:
            # Extract base message
            message = user_input.get('message', '')
            if not message and not isinstance(user_input, str):
                return {
                    "status": "error",
                    "message": "No message content provided"
                }
            
            # Initialize processed input
            processed_input = {
                "original_message": message if isinstance(message, str) else str(message),
                "type": "text",
                "metadata": {}
            }

            # Handle text-only messages
            if isinstance(user_input, str):
                processed_input["content"] = user_input
                return processed_input

            # Process attachments if present
            if 'image' in user_input:
                processed_input["type"] = "image"
                # Validate and process image
                image_data = self._process_image(user_input['image'])
                if image_data:
                    processed_input["metadata"]["image"] = image_data

            if 'receipt' in user_input:
                processed_input["type"] = "receipt"
                processed_input["metadata"]["receipt"] = user_input['receipt']

            if 'order_id' in user_input:
                processed_input["metadata"]["order_id"] = user_input['order_id']

            # Add user context if available
            if 'user_id' in user_input:
                processed_input["metadata"]["user_id"] = user_input['user_id']
            
            return processed_input

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing input: {str(e)}"
            }

    def _process_image(self, image_data: str) -> str:
        """Validate and process image data"""
        try:
            # Basic validation of base64 image data
            if not image_data.startswith('data:image/'):
                raise ValueError("Invalid image format")

            # Extract mime type and base64 data
            mime_type = image_data.split(';')[0].split(':')[1]
            if mime_type not in self.supported_image_formats:
                raise ValueError(f"Unsupported image format: {mime_type}")

            return image_data
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return None

    def format_for_operator(self, processed_input: Dict[str, Any]) -> Dict[str, Any]:
        """Format preprocessed input for operator agent"""
        return {
            "messages": [
                HumanMessage(
                    content=json.dumps(processed_input),
                    name="user_proxy"
                )
            ]
        }