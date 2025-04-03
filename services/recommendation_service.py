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
        Generate a personalized progressive learning path based on user profile and difficulty level
        
        Args:
            user_id (int): The user ID
            topic (str): The topic to create a learning path for
            difficulty (str): Starting difficulty level (beginner, intermediate, advanced)
            
        Returns:
            dict: Personalized learning path with steps and recommended courses
        """
        try:
            # Get user data to personalize the learning path
            user_data = self._get_user_data(user_id)
            
            # Adjust difficulty based on user's expertise in similar topics
            adjusted_difficulty = difficulty
            if user_data:
                # Check for strong areas that may indicate higher starting level
                strong_areas = user_data.get('strong_areas', [])
                for area in strong_areas:
                    if area.lower() in topic.lower() or topic.lower() in area.lower():
                        # User is strong in this or related topic, possibly increase difficulty
                        if difficulty == 'beginner':
                            adjusted_difficulty = 'intermediate'
                            break
            
            # Get content preferences (if user prefers videos, interactive content, etc.)
            content_preferences = {}
            if user_data:
                content_preferences = user_data.get('content_preferences', {})
            
            # Get available courses related to the topic
            # First try to find courses specifically related to the topic
            topic_courses = Course.query.filter(
                Course.title.ilike(f"%{topic}%") | 
                Course.description.ilike(f"%{topic}%")
            ).all()
            
            # If not enough topic-specific courses, include all courses
            courses = topic_courses if len(topic_courses) >= 3 else Course.query.all()
            
            if not courses:
                return {"error": "No courses available for learning path"}
            
            # Generate learning path structure using AI
            path_structure = self._generate_learning_path_structure(topic, adjusted_difficulty)
            
            # Match courses to learning path steps
            matched_path = self._match_courses_to_path(path_structure, courses)
            
            # Enhance path with estimated completion time and resource types
            enhanced_path = self._enhance_learning_path(matched_path, content_preferences)
            
            # Return the complete personalized learning path
            return {
                "topic": topic,
                "user_id": user_id,
                "starting_difficulty": adjusted_difficulty,
                "original_difficulty": difficulty,
                "estimated_total_hours": sum(step.get("estimated_hours", 2) for step in enhanced_path),
                "steps": enhanced_path
            }
            
        except Exception as e:
            logger.error(f"Error generating learning path: {str(e)}")
            return {"error": f"Failed to generate learning path: {str(e)}"}
    
    def _enhance_learning_path(self, path_steps, content_preferences=None):
        """Add enhanced metadata to learning path steps"""
        try:
            enhanced_path = []
            
            for i, step in enumerate(path_steps):
                # Estimate completion time based on difficulty and content
                difficulty = step.get("difficulty", "beginner")
                estimated_hours = 2  # Default
                
                if difficulty == "beginner":
                    estimated_hours = 1.5
                elif difficulty == "intermediate":
                    estimated_hours = 3
                elif difficulty == "advanced":
                    estimated_hours = 5
                
                # Adjust estimated time based on number of skills to learn
                skills_count = len(step.get("skills", []))
                estimated_hours += 0.5 * max(0, skills_count - 2)  # Add time for additional skills
                
                # Generate resource types based on content preferences
                recommended_resources = ["articles", "exercises"]
                if content_preferences:
                    # Add user's preferred content types as recommendations
                    preferred_types = sorted(content_preferences.items(), key=lambda x: x[1], reverse=True)
                    if preferred_types and preferred_types[0][1] > 0:
                        preferred_type = preferred_types[0][0]
                        if preferred_type == "video":
                            recommended_resources.insert(0, "video tutorials")
                        elif preferred_type == "interactive":
                            recommended_resources.insert(0, "interactive exercises")
                        elif preferred_type == "quiz":
                            recommended_resources.append("practice quizzes")
                
                # Add additional milestone or checkpoint for longer paths
                milestones = []
                if i == len(path_steps) - 1:  # Last step
                    milestones.append("Final project or assessment")
                elif i == 0:  # First step
                    milestones.append("Knowledge baseline assessment")
                elif i % 2 == 0:  # Every other step
                    milestones.append(f"Checkpoint: {step.get('title')} mastery")
                
                # Add enhanced data to the step
                enhanced_step = step.copy()
                enhanced_step.update({
                    "estimated_hours": estimated_hours,
                    "recommended_resources": recommended_resources,
                    "milestones": milestones
                })
                
                enhanced_path.append(enhanced_step)
            
            return enhanced_path
            
        except Exception as e:
            logger.error(f"Error enhancing learning path: {str(e)}")
            return path_steps  # Return original path if enhancement fails
    
    def _get_user_data(self, user_id):
        """Get comprehensive user history and preferences"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Get completed and in-progress courses with completion percentage
            completed_courses = []
            in_progress_courses = []
            
            # Get user's chat sessions to analyze interests and learning patterns
            chat_sessions = user.chat_sessions.all()
            chat_topics = []
            course_interests = set()
            
            for session in chat_sessions:
                # Extract course context if available
                if session.course_id:
                    course = Course.query.get(session.course_id)
                    if course:
                        course_interests.add(course.id)
                
                # Analyze message content to extract topics of interest
                messages = session.messages.filter_by(is_user=True).all()
                for message in messages:
                    # Identify keywords from user messages (simplified approach)
                    # In a production system, we would use NLP for keyword extraction
                    words = message.message.lower().split()
                    topics = [word for word in words if len(word) > 5]  # Simple filter for potentially meaningful words
                    chat_topics.extend(topics[:5])  # Limit to avoid noise
            
            # Get user's quiz attempts to analyze their performance
            quiz_performance = {}
            
            # Track difficult topics based on quiz performance
            weak_areas = []
            strong_areas = []
            
            # Get content engagement data - what content types the user prefers
            content_preferences = {
                "video": 0,
                "document": 0,
                "quiz": 0,
                "interactive": 0
            }
            
            # Get user's sales data if available (for sales staff learning system)
            sales_data = []
            
            # Calculate time spent on different topics/courses
            time_spent = {}
            
            # Combine into user data object with improved insight
            user_data = {
                "user_id": user_id,
                "completed_courses": completed_courses,
                "in_progress_courses": in_progress_courses,
                "quiz_performance": quiz_performance,
                "weak_areas": weak_areas,
                "strong_areas": strong_areas,
                "interests": list(set(chat_topics)),  # Deduplicate topics
                "course_interests": list(course_interests),
                "content_preferences": content_preferences,
                "time_spent": time_spent,
                "sales_data": sales_data,
                "courses": completed_courses  # Kept for backward compatibility
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
        """
        Get recommendations based on user's activity and interests
        Enhanced with content type preferences and topic analysis
        """
        try:
            # Extract all recommendation signals from the user data
            interests = user_data.get('interests', [])
            weak_areas = user_data.get('weak_areas', [])
            strong_areas = user_data.get('strong_areas', [])
            course_interests = user_data.get('course_interests', [])
            content_preferences = user_data.get('content_preferences', {})
            time_spent = user_data.get('time_spent', {})
            
            # Get in-progress courses to continue learning
            in_progress_courses = user_data.get('in_progress_courses', [])
            
            # Create a weighted recommendation strategy
            recommendations = []
            scored_courses = {}  # Store course ID to score mapping
            
            # First priority: Recommend continuing in-progress courses
            for course_id in in_progress_courses:
                course = Course.query.get(course_id)
                if course:
                    scored_courses[course.id] = 100  # Highest priority
                    recommendations.append({
                        "id": course.id,
                        "title": course.title,
                        "description": course.description,
                        "reason": "Continue your learning progress",
                        "score": 100
                    })
            
            # Second priority: Courses related to weak areas (for improvement)
            if weak_areas:
                for area in weak_areas:
                    courses = Course.query.filter(
                        Course.title.ilike(f"%{area}%") | 
                        Course.description.ilike(f"%{area}%")
                    ).all()
                    
                    for course in courses:
                        if course.id not in scored_courses:
                            score = 90
                            scored_courses[course.id] = score
                            recommendations.append({
                                "id": course.id,
                                "title": course.title,
                                "description": course.description,
                                "reason": f"To improve your understanding of {area}",
                                "score": score
                            })
            
            # Third priority: Interests from chat and behavior
            if interests:
                for interest in interests:
                    if len(interest) < 4:  # Skip very short terms
                        continue
                        
                    courses = Course.query.filter(
                        Course.title.ilike(f"%{interest}%") | 
                        Course.description.ilike(f"%{interest}%")
                    ).all()
                    
                    for course in courses:
                        if course.id not in scored_courses:
                            score = 80
                            scored_courses[course.id] = score
                            recommendations.append({
                                "id": course.id,
                                "title": course.title,
                                "description": course.description,
                                "reason": f"Based on your interest in {interest}",
                                "score": score
                            })
            
            # Fourth priority: Courses related to content user has engaged with
            if course_interests:
                for course_id in course_interests:
                    # Find related courses (e.g., sequels, same category)
                    base_course = Course.query.get(course_id)
                    if not base_course:
                        continue
                        
                    # Find courses with similar titles or descriptions
                    courses = Course.query.filter(
                        Course.id != course_id,  # Exclude the course itself
                        (Course.title.ilike(f"%{base_course.title[:10]}%") | 
                         Course.description.ilike(f"%{base_course.title[:10]}%"))
                    ).all()
                    
                    for course in courses:
                        if course.id not in scored_courses:
                            score = 70
                            scored_courses[course.id] = score
                            recommendations.append({
                                "id": course.id,
                                "title": course.title,
                                "description": course.description,
                                "reason": f"Similar to {base_course.title} course you've shown interest in",
                                "score": score
                            })
            
            # Fifth priority: Content type preferences
            # Look for courses with the user's preferred content types
            preferred_types = sorted(content_preferences.items(), key=lambda x: x[1], reverse=True)
            if preferred_types and preferred_types[0][1] > 0:
                preferred_type = preferred_types[0][0]  # Most preferred content type
                
                # Get course content with this type
                content_with_type = CourseContent.query.filter_by(content_type=preferred_type).all()
                course_ids = set(item.course_id for item in content_with_type)
                
                for course_id in course_ids:
                    course = Course.query.get(course_id)
                    if course and course.id not in scored_courses:
                        score = 60
                        scored_courses[course.id] = score
                        recommendations.append({
                            "id": course.id,
                            "title": course.title,
                            "description": course.description,
                            "reason": f"Contains {preferred_type} content you prefer",
                            "score": score
                        })
            
            # Sort recommendations by score
            recommendations.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Limit to requested number
            final_recommendations = recommendations[:limit]
            
            # If we don't have enough recommendations, add popular courses
            if len(final_recommendations) < limit:
                popular_courses = self._get_popular_courses(limit - len(final_recommendations))
                for course in popular_courses:
                    if not any(rec["id"] == course["id"] for rec in final_recommendations):
                        final_recommendations.append(course)
            
            # Remove score from the final output
            for rec in final_recommendations:
                if 'score' in rec:
                    del rec['score']
            
            return final_recommendations
            
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