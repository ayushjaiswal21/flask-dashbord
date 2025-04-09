// DOM Elements
const errorContainer = document.getElementById('errorContainer');
const quizContainer = document.getElementById('quizContainer');
let saveBtn = null; // Track save button instance

// Generate Quiz Function
async function generateQuiz() {
    const form = document.getElementById('quizForm');
    if (!form) return;

    // Clear previous save button
    if (saveBtn) {
        saveBtn.remove();
        saveBtn = null;
    }

    // Get form data with validation
    const formData = new FormData(form);
    const topics = formData.get('topics')?.split(',').map(t => t.trim()).filter(t => t) || [];
    
    // Add CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!csrfToken) {
        displayError("Security token missing. Please refresh the page.");
        return;
    }

    try {
        // Show loading state
        quizContainer.innerHTML = `<div class="loading">
            <div class="spinner"></div>
            Generating quiz questions...
        </div>`;
        clearError();

        // API request
        const response = await fetch("/api/generate-quiz", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                topics: topics,
                type: formData.get('q_type'),
                difficulty: formData.get('difficulty'),
                num_questions: parseInt(formData.get('num_questions'))
            })
        });

        // Error handling
        if (!response.ok) {
            const error = await response.json().catch(() => ({ error: "Unknown error" }));
            throw new Error(error.message || `Request failed (${response.status})`);
        }

        const data = await response.json();
        if (!data?.questions?.length) throw new Error("No questions generated");
        
        displayQuiz(data.questions, formData.get('q_type'));

    } catch (error) {
        console.error("Quiz generation error:", error);
        displayError(error.message);
        quizContainer.innerHTML = "";
    }
}

// Display Generated Quiz (Improved option parsing)
function displayQuiz(questions) {
    quizContainer.innerHTML = questions.map((q, i) => {
        const options = parseOptions(q.question);
        const isMCQ = options.length > 0;
        
        return `
            <div class="question" data-answer="${q.answer.trim().toUpperCase()}" data-index="${i}">
                <h3>Question ${i + 1}</h3>
                <div class="question-text">${escapeHTML(q.question)}</div>
                ${isMCQ ? `
                    <div class="options">
                        ${options.map((opt, j) => `
                            <div class="option">
                                <input type="radio" name="question_${i}" 
                                       id="q${i}_opt${j}" 
                                       value="${opt.letter}">
                                <label for="q${i}_opt${j}">${opt.letter}) ${opt.text}</label>
                            </div>
                        `).join('')}
                    </div>
                    <button class="btn confirm-btn" onclick="checkAnswer(${i})">
                        Check Answer
                    </button>
                    <div id="result_${i}" class="result"></div>
                ` : `
                    <details class="answer-details">
                        <summary>Show Answer</summary>
                        <div class="answer-text">${escapeHTML(q.answer)}</div>
                    </details>
                `}
            </div>
        `;
    }).join('');

    // Add save button
    if (!saveBtn) {
        saveBtn = document.createElement('button');
        saveBtn.id = 'saveQuizBtn';
        saveBtn.className = 'btn btn-primary mt-3';
        saveBtn.textContent = 'Save Quiz';
        saveBtn.onclick = saveQuiz;
        quizContainer.after(saveBtn);
    }
}

// Improved option parsing
function parseOptions(questionText) {
    const optionRegex = /^([A-E])[).]\s*(.+)$/gm;
    const matches = [];
    let match;
    
    while ((match = optionRegex.exec(questionText)) !== null) {
        matches.push({
            letter: match[1].toUpperCase(),
            text: match[2].trim()
        });
    }
    return matches;
}

// Enhanced answer checking
function checkAnswer(index) {
    const questionEl = document.querySelector(`.question[data-index="${index}"]`);
    const selected = questionEl.querySelector('input:checked');
    const resultEl = document.getElementById(`result_${index}`);
    
    if (!selected) {
        resultEl.textContent = "Please select an answer!";
        resultEl.className = "result error";
        return;
    }

    const correct = selected.value === questionEl.dataset.answer;
    resultEl.textContent = correct 
        ? "✓ Correct!" 
        : `✗ Incorrect. Correct answer: ${questionEl.dataset.answer}`;
    resultEl.className = `result ${correct ? 'correct' : 'incorrect'}`;
    
    // Visual feedback
    questionEl.classList.add(correct ? 'answered-correct' : 'answered-wrong');
    questionEl.querySelectorAll('input').forEach(i => i.disabled = true);
}

// Enhanced save function
async function saveQuiz() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!csrfToken) {
        displayError("Security token missing. Please refresh.");
        return;
    }

    const questions = Array.from(document.querySelectorAll('.question')).map(q => ({
        text: q.querySelector('.question-text').textContent,
        options: Array.from(q.querySelectorAll('.option label')).map(l => l.textContent.trim()),
        correct_answer: q.dataset.answer
    }));

    try {
        saveBtn.disabled = true;
        saveBtn.textContent = "Saving...";
        
        const response = await fetch('/quizzes/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                title: document.getElementById('quizTitle')?.value || "Untitled Quiz",
                description: document.getElementById('quizDesc')?.value || "",
                questions: questions
            })
        });

        if (!response.ok) throw new Error(`Save failed: ${response.status}`);
        window.location.href = '/quizzes';

    } catch (error) {
        console.error("Save error:", error);
        displayError(error.message);
        saveBtn.disabled = false;
        saveBtn.textContent = "Save Quiz";
    }
}

// Error handling utilities
function displayError(message, duration = 5000) {
    if (!errorContainer) return;
    errorContainer.innerHTML = `
        <div class="alert error">
            <span class="close-btn">&times;</span>
            ${escapeHTML(message)}
        </div>
    `;
    errorContainer.querySelector('.close-btn').onclick = clearError;
    setTimeout(clearError, duration);
}

function clearError() {
    errorContainer.innerHTML = '';
}

// Security and UI helpers
function escapeHTML(str) {
    return str.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Tab switching (updated to match HTML)
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(c => 
                c.classList.toggle('active', c.id === target)
            );
            document.querySelectorAll('.tab-btn').forEach(b => 
                b.classList.toggle('active', b === this)
            );
        });
    });

    // Form handling
    document.getElementById('quizForm')?.addEventListener('submit', e => {
        e.preventDefault();
        generateQuiz();
    });
});