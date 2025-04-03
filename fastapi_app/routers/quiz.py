"""Quiz API router."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from ..database import get_db
from models import Quiz, QuizQuestion, QuizOption, Course

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/quiz/generate")
async def generate_quiz(
    course_id: int,
    title: str,
    description: str,
    num_questions: int = 5,
    db: Session = Depends(get_db)
):
    """
    Generate a quiz for a course.
    
    Args:
        course_id: Course ID
        title: Quiz title
        description: Quiz description
        num_questions: Number of questions to generate
        db: Database session
        
    Returns:
        Generated quiz details
    """
    try:
        # Check if course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course with ID {course_id} not found"
            )
            
        # In a real implementation, call AI service to generate questions
        # For now, create a simple quiz with placeholder questions
        quiz = Quiz(
            course_id=course_id,
            title=title,
            description=description
        )
        db.add(quiz)
        db.flush()  # Get quiz ID
        
        # Create placeholder questions
        for i in range(1, num_questions + 1):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=f"Sample question {i} for {course.title}",
                question_type="multiple_choice"
            )
            db.add(question)
            db.flush()  # Get question ID
            
            # Add options
            for j in range(1, 5):  # 4 options per question
                option = QuizOption(
                    question_id=question.id,
                    option_text=f"Option {j} for question {i}",
                    is_correct=(j == 1)  # First option is correct
                )
                db.add(option)
                
        db.commit()
        
        return {
            "id": quiz.id,
            "course_id": quiz.course_id,
            "title": quiz.title,
            "description": quiz.description,
            "num_questions": num_questions,
            "message": f"Quiz '{title}' generated successfully"
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating quiz: {str(e)}"
        )


@router.get("/quiz/{quiz_id}")
async def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a quiz with all questions and options.
    
    Args:
        quiz_id: Quiz ID
        db: Database session
        
    Returns:
        Quiz details with questions and options
    """
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(
                status_code=404,
                detail=f"Quiz with ID {quiz_id} not found"
            )
            
        # Get questions and options
        questions = []
        quiz_questions = db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz_id
        ).all()
        
        for question in quiz_questions:
            options = db.query(QuizOption).filter(
                QuizOption.question_id == question.id
            ).all()
            
            questions.append({
                "id": question.id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "options": [
                    {
                        "id": option.id,
                        "option_text": option.option_text,
                        "is_correct": option.is_correct
                    }
                    for option in options
                ]
            })
            
        return {
            "id": quiz.id,
            "course_id": quiz.course_id,
            "title": quiz.title,
            "description": quiz.description,
            "created_at": quiz.created_at,
            "questions": questions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting quiz: {str(e)}"
        )


@router.post("/quiz/{quiz_id}/evaluate")
async def evaluate_quiz(
    quiz_id: int,
    answers: Dict[str, int],
    db: Session = Depends(get_db)
):
    """
    Evaluate a quiz attempt.
    
    Args:
        quiz_id: Quiz ID
        answers: Dict mapping question IDs to selected option IDs
        db: Database session
        
    Returns:
        Evaluation results with score and feedback
    """
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(
                status_code=404,
                detail=f"Quiz with ID {quiz_id} not found"
            )
            
        # Validate answers
        results = {}
        correct_count = 0
        total_questions = 0
        
        for question_id_str, option_id in answers.items():
            try:
                question_id = int(question_id_str)
                # Check if question exists and belongs to the quiz
                question = db.query(QuizQuestion).filter(
                    QuizQuestion.id == question_id,
                    QuizQuestion.quiz_id == quiz_id
                ).first()
                
                if not question:
                    continue
                    
                # Get correct option
                correct_option = db.query(QuizOption).filter(
                    QuizOption.question_id == question_id,
                    QuizOption.is_correct == True
                ).first()
                
                if not correct_option:
                    continue
                    
                total_questions += 1
                is_correct = (option_id == correct_option.id)
                
                if is_correct:
                    correct_count += 1
                    
                results[question_id] = {
                    "is_correct": is_correct,
                    "selected_option": option_id,
                    "correct_option": correct_option.id,
                    "explanation": f"The correct answer is: {correct_option.option_text}"
                }
            except ValueError:
                # Skip invalid question IDs
                continue
                
        # Calculate score
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        return {
            "quiz_id": quiz_id,
            "score": score_percentage,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "results": results,
            "feedback": f"You scored {score_percentage:.1f}% ({correct_count}/{total_questions})"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating quiz: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating quiz: {str(e)}"
        )


@router.get("/quizzes/course/{course_id}")
async def get_quizzes_for_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all quizzes for a course.
    
    Args:
        course_id: Course ID
        db: Database session
        
    Returns:
        List of quizzes for the course
    """
    try:
        # Check if course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course with ID {course_id} not found"
            )
            
        quizzes = db.query(Quiz).filter(Quiz.course_id == course_id).all()
        
        return {
            "course_id": course_id,
            "course_title": course.title,
            "quizzes": [
                {
                    "id": quiz.id,
                    "title": quiz.title,
                    "description": quiz.description,
                    "created_at": quiz.created_at
                }
                for quiz in quizzes
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quizzes for course: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting quizzes for course: {str(e)}"
        )