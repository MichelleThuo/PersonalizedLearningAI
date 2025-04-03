import logging
from models import Quiz, QuizQuestion, QuizOption, CourseContent
from app import db
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class QuizService:
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def create_quiz(self, course_id, title, description, content_ids=None):
        """
        Create a new quiz for a course, optionally based on specific content
        
        Args:
            course_id (int): The course ID
            title (str): Quiz title
            description (str): Quiz description
            content_ids (list, optional): List of content IDs to base the quiz on
            
        Returns:
            Quiz: The created quiz object or None if failed
        """
        try:
            # Create the quiz
            quiz = Quiz(
                course_id=course_id,
                title=title,
                description=description
            )
            db.session.add(quiz)
            db.session.flush()  # Get the quiz ID before committing
            
            # If content IDs provided, generate questions based on that content
            if content_ids and len(content_ids) > 0:
                # Get the content
                contents = CourseContent.query.filter(
                    CourseContent.id.in_(content_ids),
                    CourseContent.course_id == course_id
                ).all()
                
                # Combine content for context
                combined_content = ""
                for content in contents:
                    combined_content += f"{content.title}\n{content.content_text or ''}\n\n"
                
                # Generate questions using OpenAI
                questions = self.openai_service.generate_quiz(combined_content, num_questions=5)
                
                # Add questions to the quiz
                for q_data in questions:
                    question = QuizQuestion(
                        quiz_id=quiz.id,
                        question_text=q_data['question'],
                        question_type='multiple_choice'
                    )
                    db.session.add(question)
                    db.session.flush()
                    
                    # Add options
                    for i, option_text in enumerate(q_data['options']):
                        option = QuizOption(
                            question_id=question.id,
                            option_text=option_text,
                            is_correct=(i == q_data['correct_index'])
                        )
                        db.session.add(option)
            
            db.session.commit()
            return quiz
            
        except Exception as e:
            logger.error(f"Error creating quiz: {str(e)}")
            db.session.rollback()
            return None
    
    def get_quiz(self, quiz_id):
        """
        Get a quiz with all questions and options
        
        Args:
            quiz_id (int): The quiz ID
            
        Returns:
            dict: Quiz data with questions and options
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return None
            
            # Format quiz data
            quiz_data = {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'course_id': quiz.course_id,
                'questions': []
            }
            
            # Get questions
            questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
            
            for question in questions:
                q_data = {
                    'id': question.id,
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'options': []
                }
                
                # Get options
                options = QuizOption.query.filter_by(question_id=question.id).all()
                
                for option in options:
                    q_data['options'].append({
                        'id': option.id,
                        'option_text': option.option_text,
                        'is_correct': option.is_correct
                    })
                
                quiz_data['questions'].append(q_data)
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error getting quiz: {str(e)}")
            return None
    
    def evaluate_quiz_attempt(self, quiz_id, answers):
        """
        Evaluate a user's quiz attempt
        
        Args:
            quiz_id (int): The quiz ID
            answers (dict): Dictionary mapping question IDs to selected option IDs
            
        Returns:
            dict: Results with score and feedback
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return None
            
            total_questions = 0
            correct_answers = 0
            feedback = []
            
            for question_id, selected_option_id in answers.items():
                question = QuizQuestion.query.get(question_id)
                if not question or question.quiz_id != quiz_id:
                    continue
                
                total_questions += 1
                
                # Get correct option
                correct_option = QuizOption.query.filter_by(
                    question_id=question_id, 
                    is_correct=True
                ).first()
                
                # Get selected option
                selected_option = QuizOption.query.get(selected_option_id)
                
                # Check if answer is correct
                is_correct = selected_option and selected_option.is_correct
                
                if is_correct:
                    correct_answers += 1
                
                feedback.append({
                    'question_id': question_id,
                    'question_text': question.question_text,
                    'is_correct': is_correct,
                    'selected_option': selected_option.option_text if selected_option else None,
                    'correct_option': correct_option.option_text if correct_option else None
                })
            
            # Calculate score
            score = 0 if total_questions == 0 else (correct_answers / total_questions) * 100
            
            return {
                'quiz_id': quiz_id,
                'total_questions': total_questions,
                'correct_answers': correct_answers,
                'score': score,
                'feedback': feedback
            }
            
        except Exception as e:
            logger.error(f"Error evaluating quiz attempt: {str(e)}")
            return None
