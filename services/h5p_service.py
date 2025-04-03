"""
H5P Content Generation Service
Provides functionality to generate H5P content from regular course content
"""

import json
import logging
import os
import re
import uuid
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
import base64
from flask import current_app
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class H5PService:
    """Service for generating H5P content"""
    
    def __init__(self):
        # Use Hugging Face API through our existing OpenAI service class
        self.ai_service = OpenAIService()
        self.h5p_temp_dir = os.path.join(os.getcwd(), 'static', 'h5p_content')
        
        # Create temp directory if it doesn't exist
        if not os.path.exists(self.h5p_temp_dir):
            os.makedirs(self.h5p_temp_dir)
    
    def generate_interactive_content(self, content_text, content_type="course_presentation"):
        """
        Generate H5P interactive content based on course content
        
        Args:
            content_text (str): The course content text
            content_type (str): H5P content type (course_presentation, interactive_video, etc.)
            
        Returns:
            dict: Generation result with file path or error
        """
        try:
            # Choose appropriate H5P generation method based on content type
            if content_type == "course_presentation":
                return self.generate_course_presentation(content_text)
            elif content_type == "question_set":
                return self.generate_question_set(content_text)
            elif content_type == "interactive_video":
                # This would require a video URL to enhance
                return {"error": "Interactive video generation requires a video URL"}
            elif content_type == "fill_in_the_blanks":
                return self.generate_fill_in_the_blanks(content_text)
            else:
                return {"error": f"Unsupported H5P content type: {content_type}"}
        
        except Exception as e:
            logger.error(f"Error generating H5P content: {str(e)}")
            return {"error": f"Failed to generate H5P content: {str(e)}"}
    
    def generate_course_presentation(self, content_text):
        """
        Generate an H5P course presentation from content
        
        Args:
            content_text (str): The course content text
            
        Returns:
            dict: Generation result with file path or error
        """
        try:
            # Generate slide content using AI
            slides = self._generate_slides_with_ai(content_text)
            
            if not slides:
                return {"error": "Failed to generate slide content"}
            
            # Create H5P structure
            h5p_json = self._create_course_presentation_structure(slides)
            
            # Generate H5P package
            package_result = self._create_h5p_package(h5p_json, "course_presentation")
            
            return package_result
        
        except Exception as e:
            logger.error(f"Error generating course presentation: {str(e)}")
            return {"error": f"Failed to generate course presentation: {str(e)}"}
    
    def generate_question_set(self, content_text):
        """
        Generate an H5P question set from content
        
        Args:
            content_text (str): The course content text
            
        Returns:
            dict: Generation result with file path or error
        """
        try:
            # Generate questions from content using AI
            questions = self.ai_service.generate_quiz(content_text, num_questions=5)
            
            if not questions:
                return {"error": "Failed to generate questions"}
            
            # Create H5P structure
            h5p_json = self._create_question_set_structure(questions)
            
            # Generate H5P package
            package_result = self._create_h5p_package(h5p_json, "question_set")
            
            return package_result
        
        except Exception as e:
            logger.error(f"Error generating question set: {str(e)}")
            return {"error": f"Failed to generate question set: {str(e)}"}
    
    def _generate_slides_with_ai(self, content_text):
        """
        Use AI to generate slide content from text
        
        Args:
            content_text (str): The course content text
            
        Returns:
            list: List of slide content objects
        """
        try:
            # Create a prompt for slide generation
            prompt = f"""Create a course presentation with slides based on the following content:

{content_text}

Format the response as a JSON array of slide objects, each with a title and content. Make it educational and engaging.
Include 3-6 slides depending on the content length.

Example format:
[
  {{
    "title": "Introduction to Topic",
    "content": "Main points for this slide...",
    "key_points": ["Point 1", "Point 2", "Point 3"]
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
                    slides = json.loads(json_str)
                    return slides
                else:
                    logger.error("Could not find valid JSON array in response")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from response: {str(e)}")
                return []
        
        except Exception as e:
            logger.error(f"Error generating slides with AI: {str(e)}")
            return []
    
    def _create_course_presentation_structure(self, slides):
        """
        Create H5P course presentation JSON structure
        
        Args:
            slides (list): List of slide content objects
            
        Returns:
            dict: H5P content structure
        """
        # Base H5P structure for course presentation
        h5p_structure = {
            "presentation": {
                "slides": []
            },
            "l10n": {
                "slide": "Slide",
                "yourScore": "Your Score",
                "maxScore": "Maximum Score",
                "goodScore": "Congratulations! You got @score out of @total points!",
                "okScore": "Nice effort! You got @score out of @total points.",
                "badScore": "You got @score out of @total points.",
                "retry": "Retry",
                "title": "Course Presentation",
                "author": "Author",
                "exitFullscreen": "Exit Fullscreen",
                "fullscreen": "Fullscreen",
                "prevSlide": "Previous Slide",
                "nextSlide": "Next Slide",
                "slide": "Slide",
                "yourScore": "Your Score",
                "maxScore": "Maximum Score",
                "goodScore": "Congratulations! You got @score out of @total points!",
                "okScore": "Nice effort! You got @score out of @total points.",
                "badScore": "You got @score out of @total points.",
                "retry": "Retry"
            }
        }
        
        # Add slides to structure
        for slide_data in slides:
            slide = {
                "elements": [
                    # Slide title
                    {
                        "x": 0,
                        "y": 0,
                        "width": 100,
                        "height": 15,
                        "action": {
                            "library": "H5P.Text 1.1",
                            "params": {
                                "text": f"<h2>{slide_data['title']}</h2>"
                            },
                            "subContentId": str(uuid.uuid4())
                        }
                    },
                    # Slide content
                    {
                        "x": 0,
                        "y": 20,
                        "width": 100,
                        "height": 60,
                        "action": {
                            "library": "H5P.Text 1.1",
                            "params": {
                                "text": f"<p>{slide_data['content']}</p>"
                            },
                            "subContentId": str(uuid.uuid4())
                        }
                    }
                ],
                "keywords": []
            }
            
            # Add key points if available
            if "key_points" in slide_data and slide_data["key_points"]:
                key_points_html = "<ul>"
                for point in slide_data["key_points"]:
                    key_points_html += f"<li>{point}</li>"
                key_points_html += "</ul>"
                
                slide["elements"].append({
                    "x": 0,
                    "y": 70,
                    "width": 100,
                    "height": 25,
                    "action": {
                        "library": "H5P.Text 1.1",
                        "params": {
                            "text": key_points_html
                        },
                        "subContentId": str(uuid.uuid4())
                    }
                })
            
            h5p_structure["presentation"]["slides"].append(slide)
        
        return h5p_structure
    
    def _create_question_set_structure(self, questions):
        """
        Create H5P question set JSON structure
        
        Args:
            questions (list): List of question objects
            
        Returns:
            dict: H5P content structure
        """
        # Base H5P structure for question set
        h5p_structure = {
            "introPage": {
                "showIntroPage": True,
                "title": "Interactive Quiz",
                "introduction": "Answer the following questions to test your knowledge.",
                "startButtonText": "Start Quiz"
            },
            "progressType": "dots",
            "passPercentage": 50,
            "questions": [],
            "l10n": {
                "question": "Question",
                "of": "of",
                "nextButton": "Next question",
                "showResults": "Show results",
                "retryButton": "Retry",
                "finishButton": "Finish",
                "textualProgress": "Question: @current of @total questions",
                "scoreText": "@score / @total",
                "resultText": "You got @score out of @total points",
                "resultAlmostText": "You almost got it!",
                "resultGotText": "You got it!",
                "failText": "You failed",
                "tryAgain": "Try again",
                "fullScreenInformation": "Click to go fullscreen"
            }
        }
        
        # Add questions to structure
        for q_data in questions:
            # Create options
            alternatives = []
            for i, option_text in enumerate(q_data["options"]):
                alternatives.append({
                    "text": option_text,
                    "correct": i == q_data["correct_index"],
                    "tipsAndFeedback": {
                        "tip": "",
                        "chosenFeedback": "",
                        "notChosenFeedback": ""
                    }
                })
            
            question = {
                "library": "H5P.MultiChoice 1.14",
                "params": {
                    "question": q_data["question"],
                    "answers": alternatives,
                    "behaviour": {
                        "enableRetry": True,
                        "enableSolutionsButton": True,
                        "singlePoint": True,
                        "randomAnswers": True,
                        "showSolutionsRequiresInput": True,
                        "confirmCheckDialog": False,
                        "confirmRetryDialog": False,
                        "autoCheck": False,
                        "passPercentage": 50,
                        "showScorePoints": True
                    }
                }
            }
            
            h5p_structure["questions"].append(question)
        
        return h5p_structure
    
    def _create_h5p_package(self, content_json, content_type):
        """
        Create H5P package file
        
        Args:
            content_json (dict): H5P content structure
            content_type (str): H5P content type
            
        Returns:
            dict: Result with file path or error
        """
        try:
            # Create unique filename
            filename = f"{content_type}_{uuid.uuid4()}.h5p"
            file_path = os.path.join(self.h5p_temp_dir, filename)
            
            # Create in-memory zip file
            zip_buffer = BytesIO()
            
            with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as h5p_zip:
                # Add content.json
                h5p_zip.writestr('content/content.json', json.dumps(content_json))
                
                # Add h5p.json (package metadata)
                h5p_metadata = {
                    "title": f"Generated {content_type.replace('_', ' ').title()}",
                    "language": "en",
                    "mainLibrary": self._get_main_library(content_type),
                    "preloadedDependencies": self._get_dependencies(content_type)
                }
                h5p_zip.writestr('h5p.json', json.dumps(h5p_metadata))
            
            # Save the zip file
            with open(file_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
            
            return {
                "success": True,
                "file_path": file_path,
                "url": f"/static/h5p_content/{filename}"
            }
            
        except Exception as e:
            logger.error(f"Error creating H5P package: {str(e)}")
            return {"error": f"Failed to create H5P package: {str(e)}"}
    
    def _get_main_library(self, content_type):
        """Get the main H5P library for the content type"""
        if content_type == "course_presentation":
            return "H5P.CoursePresentation 1.22"
        elif content_type == "question_set":
            return "H5P.QuestionSet 1.17"
        elif content_type == "interactive_video":
            return "H5P.InteractiveVideo 1.22"
        elif content_type == "fill_in_the_blanks":
            return "H5P.Blanks 1.12"
        else:
            return "H5P.CoursePresentation 1.22"  # default
    
    def generate_fill_in_the_blanks(self, content_text):
        """
        Generate an H5P fill-in-the-blanks exercise from content
        
        Args:
            content_text (str): The course content text
            
        Returns:
            dict: Generation result with file path or error
        """
        try:
            # Generate fill-in-the-blanks sentences using AI
            sentences = self._generate_blanks_with_ai(content_text)
            
            if not sentences:
                return {"error": "Failed to generate fill-in-the-blanks content"}
            
            # Create H5P structure
            h5p_json = self._create_blanks_structure(sentences)
            
            # Generate H5P package
            package_result = self._create_h5p_package(h5p_json, "fill_in_the_blanks")
            
            return package_result
        
        except Exception as e:
            logger.error(f"Error generating fill-in-the-blanks: {str(e)}")
            return {"error": f"Failed to generate fill-in-the-blanks: {str(e)}"}
    
    def _generate_blanks_with_ai(self, content_text):
        """
        Use AI to generate fill-in-the-blanks sentences from text
        
        Args:
            content_text (str): The course content text
            
        Returns:
            list: List of sentence objects with blanks
        """
        try:
            # Create a prompt for fill-in-the-blanks generation
            prompt = f"""Create 5-8 fill-in-the-blanks sentences based on the following content:

{content_text}

For each sentence, identify key terms to blank out. Format the response as a JSON array of sentence objects.
Each sentence should have:
1. The full text with blanks indicated by "*blank*" (e.g. "The capital of France is *blank*.")
2. An array of correct answers for each blank

Example format:
[
  {{
    "text": "The capital of France is *blank*.",
    "answers": ["Paris"]
  }},
  {{
    "text": "HTML stands for *blank* *blank* *blank*.",
    "answers": ["Hypertext", "Markup", "Language"]
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
                    sentences = json.loads(json_str)
                    return sentences
                else:
                    logger.error("Could not find valid JSON array in response")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from response: {str(e)}")
                return []
        
        except Exception as e:
            logger.error(f"Error generating fill-in-the-blanks with AI: {str(e)}")
            return []
    
    def _create_blanks_structure(self, sentences):
        """
        Create H5P fill-in-the-blanks JSON structure
        
        Args:
            sentences (list): List of sentence objects with blanks
            
        Returns:
            dict: H5P content structure
        """
        # Process sentences to H5P format
        task_text = ""
        for sentence in sentences:
            # Replace *blank* with H5P blanks format
            blank_count = 0
            text = sentence["text"]
            answers = sentence["answers"]
            
            for i in range(len(answers)):
                blank_placeholder = "*blank*"
                if blank_placeholder in text:
                    # Replace with H5P blank format: *answer*
                    answer = answers[blank_count]
                    blank_count += 1
                    text = text.replace(blank_placeholder, f"*{answer}*", 1)
            
            task_text += text + "\n\n"
        
        # Base H5P structure for fill-in-the-blanks
        h5p_structure = {
            "params": {
                "taskDescription": "Fill in the blanks with the correct terms.",
                "text": task_text.strip(),
                "behaviour": {
                    "enableRetry": True,
                    "enableSolutionsButton": True,
                    "enableCheckButton": True,
                    "caseSensitive": False,
                    "autoCheck": False,
                    "showSolutionsRequiresInput": True
                },
                "l10n": {
                    "checkAnswer": "Check",
                    "showSolution": "Show solution",
                    "tryAgain": "Retry",
                    "solutionButton": "Solution",
                    "correctText": "Correct!",
                    "incorrectText": "Incorrect!",
                    "missedText": "Missing!",
                    "displaySolutionDescription": "Task is updated to contain the solution."
                }
            }
        }
        
        return h5p_structure
        
    def _get_dependencies(self, content_type):
        """Get the required H5P dependencies for the content type"""
        dependencies = []
        
        # Common dependencies
        dependencies.append({"machineName": "H5P.Text", "majorVersion": 1, "minorVersion": 1})
        
        # Content-specific dependencies
        if content_type == "course_presentation":
            dependencies.append({"machineName": "H5P.CoursePresentation", "majorVersion": 1, "minorVersion": 22})
        elif content_type == "question_set":
            dependencies.append({"machineName": "H5P.QuestionSet", "majorVersion": 1, "minorVersion": 17})
            dependencies.append({"machineName": "H5P.MultiChoice", "majorVersion": 1, "minorVersion": 14})
        elif content_type == "interactive_video":
            dependencies.append({"machineName": "H5P.InteractiveVideo", "majorVersion": 1, "minorVersion": 22})
        elif content_type == "fill_in_the_blanks":
            dependencies.append({"machineName": "H5P.Blanks", "majorVersion": 1, "minorVersion": 12})
        
        return dependencies