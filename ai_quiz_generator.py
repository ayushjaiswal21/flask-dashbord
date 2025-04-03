def generate_quiz(subject, num_questions, difficulty):
    """
    Generate quiz questions using AI. This is a placeholder function.
    In a real implementation, you would call your AI model here.
    
    Returns a list of question dictionaries with format:
    {
        'question': 'What is 2+2?',
        'options': ['3', '4', '5', '6'],
        'correct_answer': '4'
    }
    """
    # Placeholder - replace with your actual AI quiz generation code
    questions = []
    
    sample_questions = {
        'math': [
            {
                'question': 'What is 2+2?',
                'options': ['3', '4', '5', '6'],
                'correct_answer': '4'
            },
            {
                'question': 'What is 5×5?',
                'options': ['20', '25', '30', '35'],
                'correct_answer': '25'
            }
        ],
        'science': [
            {
                'question': 'What is the chemical symbol for water?',
                'options': ['H2O', 'CO2', 'O2', 'N2'],
                'correct_answer': 'H2O'
            },
            {
                'question': 'What is the closest planet to the Sun?',
                'options': ['Earth', 'Venus', 'Mercury', 'Mars'],
                'correct_answer': 'Mercury'
            }
        ],
        'literature': [
            {
                'question': 'Who wrote "Romeo and Juliet"?',
                'options': ['Charles Dickens', 'William Shakespeare', 'Jane Austen', 'Mark Twain'],
                'correct_answer': 'William Shakespeare'
            },
            {
                'question': 'What is the name of the main character in "The Great Gatsby"?',
                'options': ['Jay Gatsby', 'Nick Carraway', 'Tom Buchanan', 'Daisy Buchanan'],
                'correct_answer': 'Jay Gatsby'
            }
        ]
    }
    
    # Get sample questions based on subject or use default
    subject_questions = sample_questions.get(subject.lower(), sample_questions['math'])
    
    # Return requested number of questions (or all available if less)
    return subject_questions[:min(num_questions, len(subject_questions))]