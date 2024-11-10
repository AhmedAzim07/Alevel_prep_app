import streamlit as st
from openai import OpenAI

# API key
read_api_key = st.secrets["API_KEY_ST"]

# Initialize OpenAI client
client = OpenAI(api_key=read_api_key)

# Function to query OpenAI for questions
def query_open_ai(prompt, mcq=False):
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    generated_text = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            generated_text += str(chunk.choices[0].delta.content)

    return generated_text

# Function to generate written questions
def generate_written_questions(topic):
    prompt = f"""
    You are an A-level professor. Students will give you a topic. Your job is to come up with A-level questions
    that are based on this topic. The difficulty of these questions should be per the skill level of an average
    A-level student and the questions should not be very complex. Ask 5 questions that MUST end with a question mark, this is very important.
    # Here is the topic: 
    {topic}
    """
    return query_open_ai(prompt)

# Function to generate MCQ questions
def generate_mcq_questions(topic):
    prompt = f"""
    You are an A-level professor. Create 5 multiple-choice questions (MCQs) based on the topic '{topic}' for A-level students.
    Each question should have exactly 4 answer choices labeled (A), (B), (C), and (D), with only one correct answer.
    """
    return query_open_ai(prompt)

# Function to parse MCQs into questions and answer choices
def parse_mcq_questions(mcq_text):
    questions = []
    lines = mcq_text.split("\n")
    current_question = {"question": "", "choices": [], "correct_answer": ""}
    
    for line in lines:
        if line.startswith("Q"):  # New question line
            if current_question["question"]:  # Save the last question if it exists
                questions.append(current_question)
                current_question = {"question": "", "choices": [], "correct_answer": ""}
            current_question["question"] = line
        elif line.startswith(("A)", "B)", "C)", "D)")):
            current_question["choices"].append(line)
        elif "Correct answer:" in line:
            current_question["correct_answer"] = line.split(":")[-1].strip()
    
    # Add the last question
    if current_question["question"]:
        questions.append(current_question)
    
    return questions

# Function to check MCQ answers
def check_mcq_answers(questions, selected_answers):
    results = []
    for i, question in enumerate(questions):
        correct_answer = question["correct_answer"]
        selected_answer = selected_answers[i]
        if selected_answer == correct_answer:
            results.append(f"Question {i + 1}: Correct!")
        else:
            results.append(f"Question {i + 1}: Incorrect. Correct answer: {correct_answer}")
    return results

# Function to compare answers with AI
def compare_answers_with_ai(student_answer, correct_answer):
    prompt = f"""
    You are an A-level professor. Compare the following two answers and evaluate whether the student's answer is correct, partially correct, or incorrect. Provide a brief evaluation.
    
    Student's answer: {student_answer}
    Correct answer: {correct_answer}
    
    Provide a verdict: Correct, Partially Correct, or Incorrect. Follow it with a one-sentence explanation.
    """
    return query_open_ai(prompt)

# Main function for Streamlit app
def main():
    st.title("A-level Quiz Bot")

    # Step 1: Choose between Structured Questions or MCQs
    st.subheader("Choose the type of questions:")
    choice = st.radio("Select the question type:", ("Written Questions", "MCQs"))

    # Step 2: Input topic and generate questions based on choice
    if choice == "Written Questions":
        st.subheader("Written Questions")
        topic = st.text_input('Enter the topic for written questions:')
        
        if st.button('Generate Written Questions'):
            written_questions = generate_written_questions(topic)
            st.text_area('Written Questions Generated:', written_questions, height=200)

            # Student answers input and checking logic
            st.subheader("Enter your answers below:")
            for i in range(5):
                student_answer = st.text_input(f"Answer for Question {i + 1}:", key=f"written_answer_{i}")
                correct_answer = ""  # Replace with the actual correct answer if available
                if st.button(f"Check Answer {i + 1}", key=f"check_written_answer_{i}"):
                    evaluation = compare_answers_with_ai(student_answer, correct_answer)
                    st.write(evaluation)

    
    elif choice == "MCQs":
        st.subheader("Multiple-Choice Questions (MCQs)")
        topic = st.text_input('Enter the topic for MCQs:')
        
        if st.button('Generate MCQs'):
            mcq_text = generate_mcq_questions(topic)
            questions = parse_mcq_questions(mcq_text)

            # Store questions and options in session state
            if "mcq_questions" not in st.session_state:
                st.session_state.mcq_questions = questions
                st.session_state.selected_answers = [None] * len(questions)

            # Display MCQ questions and answer choices
            st.subheader("Answer the MCQs:")
            for i, question in enumerate(st.session_state.mcq_questions):
                st.write(question["question"])
                st.session_state.selected_answers[i] = st.radio(
                    f"Select your answer for Question {i + 1}",
                    [choice.split(") ")[0] for choice in question["choices"]],
                    key=f"mcq_answer_{i}"
                )

            # Check answers
            if st.button("Check Answers"):
                results = check_mcq_answers(st.session_state.mcq_questions, st.session_state.selected_answers)
                for result in results:
                    st.write(result)

if __name__ == "__main__":
    main()
