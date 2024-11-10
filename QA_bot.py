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

            # Student answers input and checking logic (similar to existing structured question handling)

    elif choice == "MCQs":
        st.subheader("Multiple-Choice Questions (MCQs)")
        topic = st.text_input('Enter the topic for MCQs:')
        
        if st.button('Generate MCQs'):
            mcq_questions = generate_mcq_questions(topic)
            st.text_area('MCQs Generated:', mcq_questions, height=200)

            # MCQ student answers input and checking logic (specific to MCQ format)

if __name__ == "__main__":
    main()
