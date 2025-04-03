// DOM Elements
const errorContainer = document.getElementById('errorContainer');
const quizContainer = document.getElementById('quizContainer');

// Generate Quiz Function
async function generateQuiz() {
    // Get form elements
    const form = document.getElementById('quizForm');
    if (!form) return;
    
    // Get form data
    const formData = new FormData(form);
    const topics = formData.get('topics').split(',').map(t => t.trim()).filter(t => t);
    const qType = formData.get('q_type');
    const difficulty = formData.get('difficulty');
    const numQuestions = parseInt(formData.get('num_questions'));

    // Validate inputs
    if (!topics.length || !qType || !difficulty || isNaN(numQuestions)) {
        displayError("All fields are required!");
        return;
    }
    
    if (numQuestions < 1 || numQuestions > 20) {
        displayError("Please choose between 1 and 20 questions!");
        return;
    }

    try {
        // Show loading state
        quizContainer.innerHTML = "<div class='loading'>Generating quiz questions...</div>";
        clearError();

        // Prepare request data
        const requestData = {
            topics: topics,
            type: qType,
            difficulty: difficulty,
            num_questions: numQuestions
        };

        // Send request
        const response = await fetch("/api/generate-quiz-api", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(requestData),
        });

        // Handle response
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Request failed with status ${response.status}`);
        }

        const data = await response.json();
        
        if (!data.questions || !data.questions.length) {
            throw new Error("No questions were generated");
        }

        // Display the quiz
        displayQuiz(data.questions, qType);

    } catch (error) {
        console.error("Quiz generation error:", error);
        displayError(`Failed to generate quiz: ${error.message}`);
        quizContainer.innerHTML = "";
    }
}

// Display Generated Quiz
function displayQuiz(questions, questionType) {
    if (!questions.length) {
        quizContainer.innerHTML = "<p>No questions were generated</p>";
        return;
    }

    let quizHTML = '';
    
    questions.forEach((q, i) => {
        const questionText = escapeHTML(q.question || "No question text");
        const answerText = escapeHTML(q.answer || "No answer provided");
        
        let optionsHTML = '';
        let isMultipleChoice = false;
        let questionContent = questionText;
        
        // Parse multiple choice options
        const optionRegex = /([A-Da-d]\))\s*(.+?)(?=\s+[A-Da-d]\)|$)/g;
        const options = [];
        let match;
        
        while ((match = optionRegex.exec(questionText)) !== null) {
            options.push({
                letter: match[1].charAt(0).toUpperCase(),
                text: match[2].trim()
            });
            questionContent = questionContent.replace(match[0], '');
        }
        
        // Build options HTML if multiple choice
        if (options.length > 0) {
            isMultipleChoice = true;
            options.forEach(opt => {
                optionsHTML += `
                    <div class="option">
                        <input type="radio" name="question_${i}" id="q${i}_opt${opt.letter}" value="${opt.letter}">
                        <label for="q${i}_opt${opt.letter}">${opt.letter}) ${opt.text}</label>
                    </div>
                `;
            });
        }
        
        // Build question HTML
        quizHTML += `
            <div class="question" data-answer="${answerText.trim().toUpperCase()}" data-index="${i}">
                <h3>Question ${i + 1}:</h3>
                <div class="question-text">${questionContent}</div>
                
                ${isMultipleChoice ? `
                    <div class="options">${optionsHTML}</div>
                    <button class="btn btn-primary confirm-btn" onclick="checkAnswer(${i})">Check Answer</button>
                    <div id="result_${i}" class="result hidden"></div>
                ` : `
                    <details class="answer-details">
                        <summary>Show Answer</summary>
                        <div class="answer-text">${answerText}</div>
                    </details>
                `}
            </div>
        `;
    });
    
    quizContainer.innerHTML = quizHTML;
    
    // Add save button if not present
    if (!document.getElementById('saveQuizBtn')) {
        const saveBtn = document.createElement('button');
        saveBtn.id = 'saveQuizBtn';
        saveBtn.className = 'btn btn-primary';
        saveBtn.textContent = 'Save Quiz';
        saveBtn.onclick = saveQuiz;
        quizContainer.insertAdjacentElement('afterend', saveBtn);
    }
}

// Check Answer Function
function checkAnswer(questionIndex) {
    const questionEl = document.querySelector(`.question[data-index="${questionIndex}"]`);
    const selectedOption = questionEl.querySelector(`input[name="question_${questionIndex}"]:checked`);
    const correctAnswer = questionEl.dataset.answer;
    const resultEl = document.getElementById(`result_${questionIndex}`);
    
    if (!selectedOption) {
        resultEl.textContent = "Please select an answer first!";
        resultEl.className = "result error";
        resultEl.classList.remove("hidden");
        return;
    }
    
    const selectedValue = selectedOption.value.toUpperCase();
    const isCorrect = selectedValue === correctAnswer;
    
    resultEl.textContent = isCorrect 
        ? "✓ Correct!" 
        : `✗ Incorrect! The correct answer is ${correctAnswer}`;
    
    resultEl.className = isCorrect ? "result correct" : "result incorrect";
    resultEl.classList.remove("hidden");
    
    // Disable interaction after answering
    questionEl.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.disabled = true;
    });
    
    const confirmBtn = questionEl.querySelector('.confirm-btn');
    if (confirmBtn) confirmBtn.disabled = true;
}

// Save Quiz Function
async function saveQuiz() {
    const title = document.getElementById('title')?.value;
    const description = document.getElementById('description')?.value;
    
    if (!title) {
        displayError("Quiz title is required");
        return;
    }
    
    const questions = [];
    document.querySelectorAll('.question').forEach((qEl, i) => {
        const question = {
            text: qEl.querySelector('.question-text').textContent,
            options: [],
            correct_answer: qEl.dataset.answer
        };
        
        // Get options if multiple choice
        qEl.querySelectorAll('.option label').forEach(opt => {
            question.options.push(opt.textContent.trim());
        });
        
        questions.push(question);
    });
    
    try {
        const formData = new FormData();
        formData.append('title', title);
        if (description) formData.append('description', description);
        
        questions.forEach((q, i) => {
            formData.append(`question_${i+1}`, q.text);
            q.options.forEach((opt, j) => {
                formData.append(`option_${i+1}_${j+1}`, opt);
            });
            formData.append(`correct_${i+1}`, q.correct_answer);
        });
        
        const response = await fetch('/create-quiz', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to save quiz');
        }
        
        window.location.href = '/quizzes';
        
    } catch (error) {
        console.error("Save quiz error:", error);
        displayError(error.message);
    }
}

// Helper Functions
function displayError(message) {
    if (!errorContainer) return;
    errorContainer.textContent = message;
    errorContainer.classList.remove("hidden");
    setTimeout(() => errorContainer.classList.add("hidden"), 5000);
}

function clearError() {
    if (errorContainer) {
        errorContainer.textContent = "";
        errorContainer.classList.add("hidden");
    }
}

function escapeHTML(str) {
    if (!str) return "";
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Generate quiz button
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateQuiz);
    }
    
    // Form submission
    const quizForm = document.getElementById('quizForm');
    if (quizForm) {
        quizForm.addEventListener('submit', (e) => {
            e.preventDefault();
            generateQuiz();
        });
    }
    
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    if (tabBtns.length) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const tab = this.dataset.tab;
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                document.getElementById(`${tab}-tab`).classList.add('active');
            });
        });
    }
});