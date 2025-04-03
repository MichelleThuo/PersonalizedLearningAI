// Quiz functionality
document.addEventListener('DOMContentLoaded', function() {
    const generateQuizForm = document.getElementById('generate-quiz-form');
    const quizContainer = document.getElementById('quiz-container');
    const quizResultsContainer = document.getElementById('quiz-results');
    
    // Function to handle quiz generation
    function handleQuizGeneration(e) {
        if (e) e.preventDefault();
        
        const courseId = document.getElementById('quiz-course-select').value;
        const title = document.getElementById('quiz-title').value.trim();
        const description = document.getElementById('quiz-description').value.trim();
        
        // Get selected content IDs if content selector exists
        const contentIds = [];
        const contentSelect = document.getElementById('content-select');
        if (contentSelect && contentSelect.options) {
            for (let i = 0; i < contentSelect.options.length; i++) {
                if (contentSelect.options[i].selected) {
                    contentIds.push(parseInt(contentSelect.options[i].value));
                }
            }
        }
        
        if (!courseId || !title) {
            alert('Please select a course and enter a title');
            return;
        }
        
        // Show loading state
        quizContainer.innerHTML = `
            <div class="loading-container">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>Generating quiz questions...</p>
                <p class="text-muted small">This may take a moment as our AI creates questions based on the content.</p>
            </div>
        `;
        
        // Call API to generate quiz
        fetch('/api/quiz/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: parseInt(courseId),
                title: title,
                description: description,
                content_ids: contentIds
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to generate quiz');
            }
            return response.json();
        })
        .then(data => {
            displayQuiz(data.quiz);
        })
        .catch(error => {
            quizContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    Error: ${error.message}. Please try again.
                </div>
            `;
            console.error('Error generating quiz:', error);
        });
    }
    
    // Function to display a quiz
    function displayQuiz(quiz) {
        if (!quiz || !quiz.questions || quiz.questions.length === 0) {
            quizContainer.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    No questions available for this quiz.
                </div>
            `;
            return;
        }
        
        // Create quiz HTML
        let quizHtml = `
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">${quiz.title}</h5>
                </div>
                <div class="card-body">
                    <p class="card-text">${quiz.description || ''}</p>
                    <form id="quiz-form" data-quiz-id="${quiz.id}">
        `;
        
        // Add questions
        quiz.questions.forEach((question, qIndex) => {
            quizHtml += `
                <div class="question mb-4">
                    <h6 class="mb-3">${qIndex + 1}. ${question.question_text}</h6>
                    <div class="options">
            `;
            
            // Add options
            question.options.forEach((option, oIndex) => {
                quizHtml += `
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="radio" name="question_${question.id}" 
                               id="option_${question.id}_${option.id}" value="${option.id}">
                        <label class="form-check-label" for="option_${question.id}_${option.id}">
                            ${option.option_text}
                        </label>
                    </div>
                `;
            });
            
            quizHtml += `
                    </div>
                </div>
            `;
        });
        
        quizHtml += `
                    <button type="submit" class="btn btn-primary">Submit Answers</button>
                </form>
            </div>
        </div>
        `;
        
        quizContainer.innerHTML = quizHtml;
        
        // Add submit handler for the quiz form
        const quizForm = document.getElementById('quiz-form');
        if (quizForm) {
            quizForm.addEventListener('submit', handleQuizSubmission);
        }
    }
    
    // Function to handle quiz submission
    function handleQuizSubmission(e) {
        e.preventDefault();
        
        const form = e.target;
        const quizId = form.dataset.quizId;
        
        // Collect answers
        const answers = {};
        const questions = form.querySelectorAll('.question');
        
        let allAnswered = true;
        
        questions.forEach((questionDiv, index) => {
            const questionName = questionDiv.querySelector('input[type="radio"]').name;
            const selectedOption = form.querySelector(`input[name="${questionName}"]:checked`);
            
            if (selectedOption) {
                const questionId = questionName.replace('question_', '');
                answers[questionId] = parseInt(selectedOption.value);
            } else {
                allAnswered = false;
                
                // Highlight unanswered question
                questionDiv.classList.add('unanswered');
                
                // Remove highlighting after a moment
                setTimeout(() => {
                    questionDiv.classList.remove('unanswered');
                }, 3000);
            }
        });
        
        if (!allAnswered) {
            alert('Please answer all questions');
            return;
        }
        
        // Show loading state
        quizResultsContainer.innerHTML = `
            <div class="loading-container mt-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>Evaluating your answers...</p>
            </div>
        `;
        
        // Submit answers for evaluation
        fetch('/api/quiz/evaluate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                quiz_id: parseInt(quizId),
                answers: answers
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to evaluate quiz');
            }
            return response.json();
        })
        .then(data => {
            displayQuizResults(data.results);
        })
        .catch(error => {
            quizResultsContainer.innerHTML = `
                <div class="alert alert-danger mt-4" role="alert">
                    Error: ${error.message}. Please try again.
                </div>
            `;
            console.error('Error evaluating quiz:', error);
        });
    }
    
    // Function to display quiz results
    function displayQuizResults(results) {
        if (!results) {
            quizResultsContainer.innerHTML = `
                <div class="alert alert-warning mt-4" role="alert">
                    No results available.
                </div>
            `;
            return;
        }
        
        // Create results HTML
        let resultsHtml = `
            <div class="card mt-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Quiz Results</h5>
                </div>
                <div class="card-body">
                    <div class="results-summary mb-4">
                        <h6>Score: ${results.score.toFixed(1)}%</h6>
                        <p>You answered ${results.correct_answers} out of ${results.total_questions} questions correctly.</p>
                    </div>
                    <h6>Feedback:</h6>
                    <div class="feedback-list">
        `;
        
        // Add feedback for each question
        results.feedback.forEach((item, index) => {
            const iconClass = item.is_correct ? 'text-success fa-check-circle' : 'text-danger fa-times-circle';
            
            resultsHtml += `
                <div class="feedback-item mb-3 ${item.is_correct ? 'correct' : 'incorrect'}">
                    <div class="d-flex">
                        <div class="flex-shrink-0 me-3">
                            <i class="fas ${iconClass} fa-2x"></i>
                        </div>
                        <div class="flex-grow-1">
                            <p><strong>${index + 1}. ${item.question_text}</strong></p>
                            <p>Your answer: ${item.selected_option || 'No answer'}</p>
                            ${!item.is_correct ? `<p>Correct answer: ${item.correct_option}</p>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        resultsHtml += `
                    </div>
                    <button class="btn btn-primary mt-3" onclick="window.location.reload()">Try Another Quiz</button>
                </div>
            </div>
        `;
        
        quizResultsContainer.innerHTML = resultsHtml;
        
        // Scroll to results
        quizResultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Function to load a specific quiz
    function loadQuiz(quizId) {
        // Show loading state
        quizContainer.innerHTML = `
            <div class="loading-container">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>Loading quiz...</p>
            </div>
        `;
        
        // Fetch quiz data
        fetch(`/api/quiz/${quizId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load quiz');
                }
                return response.json();
            })
            .then(data => {
                displayQuiz(data.quiz);
            })
            .catch(error => {
                quizContainer.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        Error: ${error.message}. Please try again.
                    </div>
                `;
                console.error('Error loading quiz:', error);
            });
    }
    
    // Handle quiz generation form submission
    if (generateQuizForm) {
        generateQuizForm.addEventListener('submit', handleQuizGeneration);
    }
    
    // Load quiz if quiz ID is in URL
    const urlParams = new URLSearchParams(window.location.search);
    const quizId = urlParams.get('quiz_id');
    
    if (quizId) {
        loadQuiz(quizId);
    }
    
    // Handle course selection for content dropdown
    const courseSelect = document.getElementById('quiz-course-select');
    const contentSelectContainer = document.getElementById('content-select-container');
    
    if (courseSelect && contentSelectContainer) {
        courseSelect.addEventListener('change', function() {
            const courseId = this.value;
            
            if (!courseId) {
                contentSelectContainer.innerHTML = '';
                return;
            }
            
            // Show loading state
            contentSelectContainer.innerHTML = `
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading course content...</span>
            `;
            
            // Fetch course content
            fetch(`/api/course/${courseId}/contents`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to load course content');
                    }
                    return response.json();
                })
                .then(data => {
                    // Create content select dropdown
                    let html = `
                        <label for="content-select" class="form-label">Select content to include (optional)</label>
                        <select class="form-select" id="content-select" multiple size="5">
                    `;
                    
                    data.contents.forEach(content => {
                        html += `<option value="${content.id}">${content.title}</option>`;
                    });
                    
                    html += `</select>
                        <div class="form-text">Hold Ctrl/Cmd to select multiple items</div>
                    `;
                    
                    contentSelectContainer.innerHTML = html;
                })
                .catch(error => {
                    contentSelectContainer.innerHTML = `
                        <div class="alert alert-danger" role="alert">
                            Error loading content: ${error.message}
                        </div>
                    `;
                    console.error('Error loading course content:', error);
                });
        });
    }
});
