import re
from openai import OpenAI
import streamlit as st

read_api_key = st.secrets["API_KEY_ST"]

# Created a function to get answers from open_ai so you don't have to write code repeatedly to get answers from OpenAI.
# You can call the function query_open_ai and it will return the answer 
def query_open_ai(prompt, get_answers=False):
    client = OpenAI(api_key=read_api_key)
    stream = client.chat.completions.create(
        #model="gpt-3.5-turbo",
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    generated_text = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            generated_text = generated_text + str(chunk.choices[0].delta.content)
    
    if get_answers:
        prompt_answers = f"""
        You are an A-level professor. Here are some questions for an A-level student. Provide the correct answers for each question in a simple, clear manner. 
        Questions:
        {generated_text}
        """
        stream_answers = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_answers}],
            stream=True
        )
        answers_text = ""
        for chunk in stream_answers:
            if chunk.choices[0].delta.content is not None:
                answers_text = answers_text + str(chunk.choices[0].delta.content)
        return generated_text, answers_text
    return generated_text, None

# Function to display results
def display_results(student_answers, correct_answers):
    st.subheader("Results:")
    
    # Use a regex to split answers based on patterns like A1), A2), etc.
    correct_answers_list = re.split(r'(A\d\))', correct_answers)
    
    # Clean up and reformat the answers for proper alignment
    cleaned_correct_answers = []
    current_answer = ""
    
    for part in correct_answers_list:
        if part.startswith("A"):
            if current_answer:  # If there's already an accumulated answer, save it
                cleaned_correct_answers.append(current_answer.strip())
            current_answer = part  # Start a new answer part
        else:
            current_answer += part  # Continue accumulating the answer text
    
    # Append the last accumulated answer
    if current_answer:
        cleaned_correct_answers.append(current_answer.strip())
    
    # Display the results
    for i, answer in enumerate(student_answers):
        st.write(f"Question {i+1}: Your answer - {answer}")
        if i < len(cleaned_correct_answers):
            st.write(f"Correct answer - {cleaned_correct_answers[i]}")
        else:
            st.write("Correct answer not available.")

# Main function for Streamlit app
def main():
    st.title('A-level Quiz Bot')
    st.subheader("Enter a topic and I'll ask you questions!")
    
    if "final_questions" not in st.session_state:
        st.session_state.final_questions = ""
    if "student_answers" not in st.session_state:
        st.session_state.student_answers = []
    if "correct_answers" not in st.session_state:
        st.session_state.correct_answers = ""
    
    # Text input for the question
    topic = st.text_input('Enter the topic:')

    if st.button('Enter'): 
        # CREATE A PROMPT HERE TO PASS TO THE 'query_open_ai' function
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
         
        # Call the 'query_open_ai' function and save the generated answer in the final_questions variable    
        final_questions, correct_answers = query_open_ai(prompt, get_answers=True)
        st.session_state.final_questions = final_questions
        st.session_state.correct_answers = correct_answers

    
    if st.session_state.final_questions:
        # Display the generated questions
        st.text_area('Questions Generated:', st.session_state.final_questions, height=200)

        # Allow students to answer questions
        st.subheader("Answer the questions:")
        num_questions = st.session_state.final_questions.count('?')  # Count questions based on '?' in final_questions

        # Create input fields for student answers
        for i in range(num_questions):
            answer = st.text_input(f'Answer for Question {i+1}:', key=f'answer_{i}')
            if len(st.session_state.student_answers) < num_questions:
                st.session_state.student_answers.append(answer)
            else:
                st.session_state.student_answers[i] = answer
        
        # Check answers
        if st.button('Check Answers'):
            display_results(st.session_state.student_answers, st.session_state.correct_answers)

if __name__ == "__main__":
    main()
