"""
Course Recommendation Service
Provides personalized course recommendations based on user data
"""

import logging
from collections import Counter
from models import db, User, Course, CourseContent
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class RecommendationService:
    """Service for generating personalized course recommendations"""
    
    def __init__(self):
        # Use Hugging Face API through our existing OpenAI service class
        self.ai_service = OpenAIService()
    
    def get_recommendations_for_user(self, user_id, limit=5):
        """
        Get personalized course recommendations for a user
        
        Args:
            user_id (int): The user ID
            limit (int): Maximum number of recommendations
            
        Returns:
            list: List of recommended courses
        """
        try:
            # Get user history and preferences
            user_data = self._get_user_data(user_id)
            
            if not user_data or not user_data.get('courses'):
                # If no user data, return popular courses instead
                return self._get_popular_courses(limit)
            
            # Get sales data if available
            sales_data = user_data.get('sales_data')
            
            # Generate recommendations
            if sales_data and len(sales_data) > 0:
                # If sales data is available, use that for recommendations
                recommendations = self._get_sales_based_recommendations(user_id, sales_data, limit)
            else:
                # Otherwise, use completed courses and user activity
                recommendations = self._get_activity_based_recommendations(user_id, user_data, limit)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    def generate_learning_path(self, user_id, topic, difficulty='beginner'):
        """
        Generate a progressive learning path based on difficulty level
        
        Args:
            user_id (int): The user ID
            topic (str): The topic to create a learning path for
            difficulty (str): Starting difficulty level (beginner, intermediate, advanced)
            
        Returns:
            dict: Learning path with steps and recommended courses
        """
        try:
            # Get available courses related to the topic
            courses = Course.query.all()
            if not courses:
                return {"error": "No courses available for learning path"}
            
            # Generate learning path using AI
            path_content = f"Learning path for {topic}. Starting at {difficulty} level and progressing."
            path_structure = self._generate_learning_path_structure(topic, difficulty)
            
            # Match courses to learning path steps
            matched_path = self._match_courses_to_path(path_structure, courses)
            
            # Return the complete learning path
            return {
                "topic": topic,
                "starting_difficulty": difficulty,
                "steps": matched_path
            }
            
        except Exception as e:
            logger.error(f"Error generating learning path: {str(e)}")
            return {"error": f"Failed to generate learning path: {str(e)}"}
    
    def _get_user_data(self, user_id):
        """Get user history and preferences"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Get completed courses
            completed_courses = []
            
            # Get user's quiz attempts to analyze their performance
            quiz_performance = {}
            
            # Get chat sessions to analyze interests
            chat_topics = []
            
            # Get user's sales data if available
            sales_data = []
            
            # Combine into user data object
            user_data = {
                "user_id": user_id,
                "courses": completed_courses,
                "quiz_performance": quiz_performance,
                "interests": chat_topics,
                "sales_data": sales_data
            }
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return None
    
    def _get_popular_courses(self, limit=5):
        """Get popular courses as fallback recommendations"""
        try:
            # Get all courses sorted by some popularity metric
            # For now, we'll just get the most recent courses
            courses = Course.query.order_by(Course.id.desc()).limit(limit).all()
            
            # Format courses for response
            recommended_courses = []
            for course in courses:
                recommended_courses.append({
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "reason": "Popular course"
                })
            
            return recommended_courses
            
        except Exception as e:
            logger.error(f"Error getting popular courses: {str(e)}")
            return []
    
    def _get_sales_based_recommendations(self, user_id, sales_data, limit=5):
        """Get recommendations based on user's sales data"""
        try:
            # Extract product categories or types from sales data
            products = [item['product'] for item in sales_data if 'product' in item]
            
            # Find the most common products
            product_counter = Counter(products)
            top_products = product_counter.most_common(3)
            
            # Get courses related to these products
            recommended_courses = []
            
            for product, count in top_products:
                # Search for courses related to this product
                courses = Course.query.filter(
                    Course.title.ilike(f"%{product}%") | 
                    Course.description.ilike(f"%{product}%")
                ).limit(limit).all()
                
                for course in courses:
                    # Check if course is already in recommendations
                    if not any(rec["id"] == course.id for rec in recommended_courses):
                        recommended_courses.append({
                            "id": course.id,
                            "title": course.title,
                            "description": course.description,
                            "reason": f"Based on your sales of {product}"
                        })
                        
                        # Stop if we have enough recommendations
                        if len(recommended_courses) >= limit:
                            break
                
                if len(recommended_courses) >= limit:
                    break
            
            # If we don't have enough recommendations, add some popular courses
            if len(recommended_courses) < limit:
                popular_courses = self._get_popular_courses(limit - len(recommended_courses))
                for course in popular_courses:
                    if not any(rec["id"] == course["id"] for rec in recommended_courses):
                        recommended_courses.append(course)
            
            return recommended_courses
            
        except Exception as e:
            logger.error(f"Error getting sales based recommendations: {str(e)}")
            return self._get_popular_courses(limit)  # Fallback to popular courses
    
    def _get_activity_based_recommendations(self, user_id, user_data, limit=5):
        """Get recommendations based on user's activity and interests"""
        try:
            # Combine interests from chat topics and completed courses
            interests = user_data.get('interests', [])
            
            # Analyze quiz performance to find areas for improvement
            quiz_performance = user_data.get('quiz_performance', {})
            weak_areas = []
            
            for quiz_id, score in quiz_performance.items():
                if score < 0.7:  # Less than 70% score
                    # Find the quiz and its related course/content
                    # This is a simplified approach
                    weak_areas.append(f"quiz_{quiz_id}")
            
            # Combine all factors for recommendations
            factors = interests + weak_areas
            
            if not factors:
                return self._get_popular_courses(limit)
            
            # Get recommendations based on interests and weak areas
            recommended_courses = []
            
            for factor in factors:
                # Search for courses related to this factor
                courses = Course.query.filter(
                    Course.title.ilike(f"%{factor}%") | 
                    Course.description.ilike(f"%{factor}%")
                ).limit(limit).all()
                
                for course in courses:
                    # Check if course is already in recommendations
                    if not any(rec["id"] == course.id for rec in recommended_courses):
                        reason = "Based on your interests"
                        if factor.startswith("quiz_"):
                            reason = "To help improve your quiz performance"
                        
                        recommended_courses.append({
                            "id": course.id,
                            "title": course.title,
                            "description": course.description,
                            "reason": reason
                        })
                        
                        # Stop if we have enough recommendations
                        if len(recommended_courses) >= limit:
                            break
                
                if len(recommended_courses) >= limit:
                    break
            
            # If we don't have enough recommendations, add some popular courses
            if len(recommended_courses) < limit:
                popular_courses = self._get_popular_courses(limit - len(recommended_courses))
                for course in popular_courses:
                    if not any(rec["id"] == course["id"] for rec in recommended_courses):
                        recommended_courses.append(course)
            
            return recommended_courses
            
        except Exception as e:
            logger.error(f"Error getting activity based recommendations: {str(e)}")
            return self._get_popular_courses(limit)  # Fallback to popular courses
    
    def _generate_learning_path_structure(self, topic, starting_difficulty):
        """Generate learning path structure using AI"""
        try:
            # Create a prompt for learning path generation
            prompt = f"""Create a progressive learning path for the topic: {topic}.
Starting at {starting_difficulty} level and progressing to more advanced levels.

The learning path should include 4-6 steps, each with:
1. A title/name for the step
2. Skills or concepts to learn
3. Difficulty level (beginner, intermediate, advanced)
4. Prerequisites from earlier steps

Format the response as a JSON array of steps.

Example format:
[
  {{
    "step": 1,
    "title": "Introduction to {topic}",
    "skills": ["Basic concept 1", "Basic concept 2"],
    "difficulty": "beginner",
    "prerequisites": []
  }},
  {{
    "step": 2,
    "title": "Intermediate {topic} Concepts",
    "skills": ["Intermediate skill 1", "Intermediate skill 2"],
    "difficulty": "intermediate",
    "prerequisites": ["Basic concept 1"]
  }}
]
"""
            
            # Create payload for AI model
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 1024,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            # Query API
            response = self.ai_service._query_huggingface(payload)
            
            if not response:
                return []
            
            # Parse JSON from response
            try:
                if isinstance(response, list) and len(response) > 0:
                    text_response = response[0].get("generated_text", "")
                else:
                    text_response = response.get("generated_text", "")
                
                # Find JSON in the response
                json_start = text_response.find("[")
                json_end = text_response.rfind("]") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = text_response[json_start:json_end]
                    path_structure = eval(json_str)  # Using eval since the JSON might not be perfectly formatted
                    return path_structure
                else:
                    logger.error("Could not find valid JSON array in response")
                    return []
            except Exception as e:
                logger.error(f"Error parsing learning path from response: {str(e)}")
                return []
            
        except Exception as e:
            logger.error(f"Error generating learning path structure: {str(e)}")
            return []
    
    def _match_courses_to_path(self, path_structure, available_courses):
        """Match available courses to learning path steps"""
        try:
            matched_path = []
            
            for step in path_structure:
                step_data = {
                    "step": step["step"],
                    "title": step["title"],
                    "skills": step["skills"],
                    "difficulty": step["difficulty"],
                    "prerequisites": step["prerequisites"],
                    "recommended_courses": []
                }
                
                # Find courses that match this step's skills or title
                search_terms = [step["title"]] + step["skills"]
                
                for term in search_terms:
                    for course in available_courses:
                        # Check if course matches this term
                        if (term.lower() in course.title.lower() or 
                            (course.description and term.lower() in course.description.lower())):
                            
                            # Check if course is already recommended for this step
                            if not any(rec["id"] == course.id for rec in step_data["recommended_courses"]):
                                step_data["recommended_courses"].append({
                                    "id": course.id,
                                    "title": course.title,
                                    "description": course.description
                                })
                
                matched_path.append(step_data)
            
            return matched_path
            
        except Exception as e:
            logger.error(f"Error matching courses to path: {str(e)}")
            return path_structure  # Return original structure if matching fails