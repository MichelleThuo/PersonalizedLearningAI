import json
import os
import logging
import requests
from flask import current_app

# Using Hugging Face's Zephyr model instead of OpenAI
MODEL_ID = "HuggingFaceH4/zephyr-7b-beta"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        # We'll use HF_API_TOKEN from environment or config
        self.api_key = os.environ.get("HF_API_TOKEN") or current_app.config.get("HF_API_TOKEN")
        if not self.api_key:
            logger.warning("HF_API_TOKEN not found in environment variables")
            
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
    def _query_huggingface(self, payload):
        """Helper method to query Hugging Face API"""
        try:
            response = requests.post(API_URL, headers=self.headers, json=payload)
            response.raise_for_status()  # Raise exception for 4XX/5XX status codes
            return response.json()
        except Exception as e:
            logger.error(f"Error querying Hugging Face API: {str(e)}")
            return None
            
    def get_chat_response(self, messages, course_context=None):
        """
        Get a response from Hugging Face based on the chat history and course context
        
        Args:
            messages (list): List of message objects with role and content
            course_context (str, optional): Additional course context to help with responses
            
        Returns:
            str: AI response
        """
        try:
            # Format messages for HF Zephyr model format (similar to OpenAI)
            formatted_messages = []
            
            # Add system message with context
            system_content = ("You are an AI learning assistant for a Moodle Learning Management System. "
                             "Your purpose is to help users learn about company products, troubleshoot "
                             "issues, and improve their learning experience. Be helpful, concise, and "
                             "educational.")
            
            # Add course context if available
            if course_context:
                system_content += f"\n\nContext about the course: {course_context}"
                
            formatted_messages.append({
                "role": "system",
                "content": system_content
            })
            
            # Add user messages
            for msg in messages:
                formatted_messages.append(msg)
            
            # Create payload for Hugging Face API
            payload = {
                "inputs": {
                    "messages": formatted_messages
                },
                "parameters": {
                    "max_new_tokens": 512,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            # Query Hugging Face API
            response = self._query_huggingface(payload)
            
            if response and isinstance(response, list) and len(response) > 0:
                generated_text = response[0].get("generated_text", "")
                # Return the response content
                return generated_text
            else:
                return "I'm sorry, I couldn't generate a response at this time. Please try again later."
            
        except Exception as e:
            logger.error(f"Error getting response from Hugging Face: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request. Please try again later."
    
    def generate_quiz(self, content, num_questions=5):
        """
        Generate quiz questions based on course content
        
        Args:
            content (str): Course content to generate questions from
            num_questions (int): Number of questions to generate
            
        Returns:
            list: List of question objects with options and correct answer
        """
        try:
            # Create a prompt for quiz generation
            prompt = f"""You are an educational quiz generator. Create knowledge-testing questions based on the provided content. 
For each question, provide 4 options with exactly one correct answer. Respond in JSON format.

Generate {num_questions} multiple-choice questions based on this content:

{content}

Return your response in this JSON format:
{{
    "questions": [
        {{
            "question": "question text",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_index": 0
        }}
    ]
}}
"""
            
            # Create payload for Hugging Face API - text generation mode
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 1024,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            # Query Hugging Face API
            response = self._query_huggingface(payload)
            
            if not response:
                return []
                
            # Parse JSON from response
            try:
                # Extract the JSON part from the response
                text_response = ""
                if isinstance(response, list) and len(response) > 0:
                    if isinstance(response[0], dict):
                        text_response = response[0].get("generated_text", "")
                    else:
                        text_response = str(response[0])
                elif isinstance(response, dict):
                    text_response = response.get("generated_text", "")
                else:
                    text_response = str(response) if response else ""
                
                # Find JSON in the response
                json_start = text_response.find("{")
                json_end = text_response.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = text_response[json_start:json_end]
                    result = json.loads(json_str)
                    return result.get("questions", [])
                else:
                    logger.error("Could not find valid JSON in response")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from response: {str(e)}")
                return []
            
        except Exception as e:
            logger.error(f"Error generating quiz questions: {str(e)}")
            return []
    
    def analyze_content_for_keywords(self, content):
        """
        Extract important keywords and topics from content for better searching
        
        Args:
            content (str): The content to analyze
            
        Returns:
            list: List of keywords and topics
        """
        try:
            # Create a prompt for keyword extraction
            prompt = f"""Extract important keywords, concepts, and topics from the provided text. 
Return as a JSON array of strings.

Text to analyze:
{content}
"""
            
            # Create payload for Hugging Face API - text generation mode
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 256,
                    "temperature": 0.3,
                    "return_full_text": False
                }
            }
            
            # Query Hugging Face API
            response = self._query_huggingface(payload)
            
            if not response:
                return []
                
            # Parse JSON from response
            try:
                # Extract the JSON part from the response
                text_response = ""
                if isinstance(response, list) and len(response) > 0:
                    if isinstance(response[0], dict):
                        text_response = response[0].get("generated_text", "")
                    else:
                        text_response = str(response[0])
                elif isinstance(response, dict):
                    text_response = response.get("generated_text", "")
                else:
                    text_response = str(response) if response else ""
                
                # Find JSON in the response
                json_start = text_response.find("[")
                json_end = text_response.rfind("]") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = text_response[json_start:json_end]
                    result = json.loads(json_str)
                    return result
                else:
                    logger.error("Could not find valid JSON array in response")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from response: {str(e)}")
                return []
            
        except Exception as e:
            logger.error(f"Error analyzing content for keywords: {str(e)}")
            return []