from openai import OpenAI
import streamlit as st

def main():
    st.title('A-level Quiz Bot')
    st.subheader("Enter a topic and I'll ask you questions!")
    
    read_api_key = st.secrets["API_KEY_ST"]
    topic = st.text_input('Enter the topic:')

    if 'questions' not in st.session_state:
        st.session_state.questions = ""
    if 'expected_answers' not in st.session_state:
        st.session_state.expected_answers = []
    if 'student_answers' not in st.session_state:
        st.session_state.student_answers = {}
    if 'topic' not in st.session_state:
        st.session_state.topic = ""
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'score' not in st.session_state:
        st.session_state.score = 0

    if st.button('Enter'):
        st.session_state.topic = topic
        client = OpenAI(api_key=read_api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"""
            You are an A-level professor. Students will give you a topic. Your job is to come up with A-level questions
            that are based on this topic. The difficulty of these questions should be per the skill level of an average
            A-level student. Ask 5 questions which must end with a question mark. Also provide the correct answer for each question.
            Here is the topic: 
            {st.session_state.topic}                       
            """}]
        )

        try:
            # Extract questions and answers from the response
            st.session_state.questions = ""
            st.session_state.expected_answers = []
            for choice in response['choices']:
                response_text = choice['message']['content']
                lines = response_text.split('\n')
                for line in lines:
                    if line.strip().endswith('?'):
                        st.session_state.questions += line.strip() + '\n'
                    elif line.strip().startswith('Answer:'):
                        st.session_state.expected_answers.append(line.split('Answer:')[-1].strip())
            st.session_state.current_question = 0
            st.session_state.student_answers = {}
            st.session_state.score = 0

            # Display the generated questions
            st.text_area('Questions Generated:', st.session_state.questions, height=300)

        except Exception as e:
            st.write(f"Error accessing response content: {e}")

    # Allow students to answer questions
    st.subheader("Answer the questions:")
    questions = st.session_state.questions.split('\n')
    num_questions = len(questions) - 1  # Last element is an empty string due to split

    if num_questions > 0:
        current_q = st.session_state.current_question

        if current_q < num_questions:
            st.write(f"Question {current_q + 1}/{num_questions}: {questions[current_q]}")
            if f'answer_{current_q}' not in st.session_state:
                st.session_state[f'answer_{current_q}'] = ''
            st.session_state[f'answer_{current_q}'] = st.text_input(
                f'Answer for Question {current_q + 1}:',
                st.session_state[f'answer_{current_q}']
            )

            if st.button('Next Question'):
                st.session_state.student_answers[current_q] = st.session_state[f'answer_{current_q}']
                st.session_state.current_question += 1
                st.experimental_rerun()

        else:
            st.write("You have answered all the questions. Click 'Check Answers' to see your results.")

        # Check answers
        if st.button('Check Answers'):
            st.session_state.student_answers[current_q] = st.session_state[f'answer_{current_q}']
            st.subheader("Answer Checking Results:")
            for i in range(num_questions):
                student_answer = st.session_state.student_answers[i]
                correct_answer = st.session_state.expected_answers[i]

                # Use the model to check the similarity between student answers and expected answers
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an A-level professor."},
                        {"role": "user", "content": f"Question: {questions[i]}? Answer: {correct_answer}"},
                        {"role": "user", "content": f"Is the student's answer '{student_answer}' correct or similar to the expected answer? Answer with 'Yes' or 'No' and provide an explanation if necessary."}
                    ]
                )
                # Extract the model's response
                is_correct = response['choices'][0]['message']['content'].strip()
                
                st.write(f"Question {i+1}: Your answer - {student_answer}")
                st.write(f"Correct Answer: {correct_answer}")
                st.write(f"Is the answer correct? {is_correct}")

                if "Yes" in is_correct:
                    st.session_state.score += 1

            st.write(f"Your final score is: {st.session_state.score}/{num_questions}")

if __name__ == "__main__":
    main()
