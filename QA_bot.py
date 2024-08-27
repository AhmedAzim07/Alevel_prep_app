from openai import OpenAI
import streamlit as st

# Reading the API key from Streamlit secrets
read_api_key = st.secrets["API_KEY_ST"]

def query_open_ai(prompt, get_answers=False):
    client = OpenAI(api_key=read_api_key)
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    generated_text = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            generated_text += chunk.choices[0].delta.content.strip()
    
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
                answers_text += chunk.choices[0].delta.content.strip()
        return generated_text, answers_text.split('\n')  # Return answers as a list
    return generated_text, None

def main():
    st.title('A-level Quiz Bot')
    st.subheader("Enter a topic and I'll ask you questions!")
    
    if "final_questions" not in st.session_state:
        st.session_state.final_questions = ""
    if "student_answers" not in st.session_state:
        st.session_state.student_answers = []
    if "correct_answers" not in st.session_state:
        st.session_state.correct_answers = []
    
    topic = st.text_input('Enter the topic:')

    if st.button('Enter'):
        prompt = f"""
                You are an A-level professor. Students will give you a topic. Your job is to come up with A-level questions
                based on this topic. Ask 5 questions which MUST end with a question mark.
                Topic: {topic}
                """
        final_questions, correct_answers = query_open_ai(prompt, get_answers=True)
        st.session_state.final_questions = final_questions
        st.session_state.correct_answers = correct_answers
    
    if st.session_state.final_questions:
        st.text_area('Questions Generated:', st.session_state.final_questions, height=200)
        st.subheader("Answer the questions:")
        num_questions = len(st.session_state.correct_answers)

        for i in range(num_questions):
            st.session_state.student_answers.append(st.text_input(f'Answer for Question {i+1}:', key=f'answer_{i}'))
        
        if st.button('Check Answers'):
            st.subheader("Results:")
            if st.session_state.correct_answers:
                for i, correct_answer in enumerate(st.session_state.correct_answers):
                    user_answer = st.session_state.student_answers[i]
                    if user_answer.lower().strip() == correct_answer.lower().strip():
                        result = "Correct"
                    else:
                        result = "Wrong"
                    st.write(f"Question {i+1}: Your answer - {user_answer} ({result})")

if _name_ == "_main_":
    main()
