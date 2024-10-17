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
        questions = generated_text.split("\n")
        prompt_answers = f"""
        You are an A-level professor. Here are some questions for an A-level student. Provide the correct answers for each question in a simple, clear manner.
        """
        for question in questions:
            if question.strip():
                prompt_answers += f"Question: {question}\n"
        
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
                
        # Combine questions and answers properly
        question_answer_pairs = zip(questions, answers_text.split("\n"))
        combined_output = ""
        for question, answer in question_answer_pairs:
            combined_output += f"{question}\nCorrect answer: {answer.strip()}\n\n"
        
        return generated_text, combined_output
    
    return generated_text, None

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
        st.session_state.correct_answers = ""
    
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
        
        # Example Output:
        Q1) some question
        Q2) another question
        """
        
        # Call the 'query_open_ai' function and store the results in session state
        final_questions, correct_answers = query_open_ai(prompt, get_answers=True)
        st.session_state.final_questions = final_questions
        st.session_state.correct_answers = correct_answers
    
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
            if st.session_state.correct_answers:
                st.write(st.session_state.correct_answers)
                # Logic to display question-answer comparison can be added here

# Start the Streamlit app
if __name__ == "__main__":
    main()
