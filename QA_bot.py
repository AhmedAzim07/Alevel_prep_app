from openai import OpenAI
import streamlit as st

# API key
read_api_key = st.secrets["API_KEY_ST"]

# Function to query OpenAI using streaming
def query_open_ai(prompt, get_answers=False):
    # Initialize OpenAI client
    client = OpenAI(api_key=read_api_key)
    
    # Create a streaming completion request to OpenAI
    stream = client.chat.completions.create(
        model="gpt-4o-mini",  # Use gpt-3.5-turbo if needed
        messages=[{"role": "user", "content": prompt}],
        stream=True  # Streaming mode on
    )
    
    # Initialize empty string to accumulate generated text
    generated_text = ""
    
    # Streaming and collecting content chunks
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            generated_text += str(chunk.choices[0].delta.content)
    
    # Optionally generate answers based on the generated text
    if get_answers:
        # Split questions for better structure
        questions = [q for q in generated_text.split("\n") if q.strip()]  # Clean up empty lines
        
        prompt_answers = "You are an A-level professor. Provide the correct answers for the following questions in a simple, clear manner:\n"
        
        # Create a structured prompt for answers
        for question in questions:
            if question.strip():
                prompt_answers += f"{question}\n"
        
        # Request answers for each question
        stream_answers = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_answers}],
            stream=True
        )
        
        # Initialize empty string to accumulate the answers
        answers_text = ""
        for chunk in stream_answers:
            if chunk.choices[0].delta.content is not None:
                answers_text += str(chunk.choices[0].delta.content)
        
        # Split answers by lines and ensure pairing
        answers = [a for a in answers_text.split("\n") if a.strip()]

        # Combine questions with their respective answers properly
        combined_output = ""
        clean_answers = []  # To store only correct answers
        for i, question in enumerate(questions):
            combined_output += f"Q{i+1}) {question}\n"
            correct_answer = answers[i] if i < len(answers) else 'Answer not available'
            combined_output += f"Correct answer: {correct_answer}\n\n"
            clean_answers.append(correct_answer)
        
        return generated_text, combined_output, clean_answers
    
    return generated_text, None, None

# Function to compare answers using OpenAI
def compare_answers_with_ai(student_answer, correct_answer):
    # Initialize prompt for comparison
    prompt = f"""
    You are an A-level professor. Compare the following two answers and evaluate whether the student's answer is correct, partially correct, or incorrect. Provide a brief evaluation.
    
    Student's answer: {student_answer}
    Correct answer: {correct_answer}
    
    Provide a verdict: Correct, Partially Correct, or Incorrect. Follow it with a one-sentence explanation.
    """
    
    # Query OpenAI for evaluation
    evaluation, _ = query_open_ai(prompt)  # Only take the first returned value
    return evaluation

# Main function for Streamlit app
def main():
    st.title('A-level Quiz Bot')
    st.subheader("Enter a topic and I'll ask you questions!")
    
    # Initialize session state to store questions, student answers, and correct answers
    if "final_questions" not in st.session_state:
        st.session_state.final_questions = ""
    if "student_answers" not in st.session_state:
        st.session_state.student_answers = []
    if "correct_answers" not in st.session_state:
        st.session_state.correct_answers = []
    
    # Text input for the question topic
    topic = st.text_input('Enter the topic:')
    
    if st.button('Enter'):
        # Create prompt to generate questions
        prompt = f"""
        You are an A-level professor. Students will give you a topic. Your job is to come up with A-level questions
        that are based on this topic. The difficulty of these questions should be per the skill level of an average
        A-level student. Ask 5 questions which MUST end with a question mark, this is very important.
        
        # Here is the topic: 
        {topic}
        """
        
        # Call the 'query_open_ai' function and store the results in session state
        final_questions, correct_answers_output, clean_correct_answers = query_open_ai(prompt, get_answers=True)
        st.session_state.final_questions = final_questions
        st.session_state.correct_answers = clean_correct_answers
    
    if st.session_state.final_questions:
        # Display generated questions
        st.text_area('Questions Generated:', st.session_state.final_questions, height=200)
        
        # Allow students to answer questions
        st.subheader("Answer the questions:")
        num_questions = st.session_state.final_questions.count('?')  # Count questions based on '?'
        
        # Create input fields for student answers
        for i in range(num_questions):
            answer = st.text_input(f'Answer for Question {i+1}:', key=f'answer_{i}')
            if len(st.session_state.student_answers) < num_questions:
                st.session_state.student_answers.append(answer)
            else:
                st.session_state.student_answers[i] = answer
        
        # Button to check answers
        if st.button('Check Answers'):
            st.subheader("Results:")
            for i in range(num_questions):
                # Compare student's answer with correct answer using AI
                student_answer = st.session_state.student_answers[i]
                correct_answer = st.session_state.correct_answers[i]
                evaluation = compare_answers_with_ai(student_answer, correct_answer)
                
                st.write(f"Question {i+1}:")
                st.write(f"Your answer - {student_answer}")
                st.write(f"Correct answer - {correct_answer}")
                st.write(f"Evaluation: {evaluation}")

# Start the Streamlit app
if __name__ == "__main__":
    main()
