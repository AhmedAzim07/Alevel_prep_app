


from openai import OpenAI
import streamlit as st

def main():
    st.title('Alevel Prep App')
    
    read_api_key= st.secrets["API_KEY_ST"]
    # Text input for the question
    topic = st.text_input('Enter the topic:')

    if st.button('Enter'):
        client = OpenAI(api_key=read_api_key)
        stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content":
        f"""
        You are an A-level professor. Students will give you a topic. Your job is to come up with A-level questions
        that are based on this topic. The difficulty of these questions should be per the skill level of an average
        A-level student. Ask 5-10 questions
        Here is the topic: 
        {topic}           
                   
        """           
                    }],
        stream=True,
        )
        final_ans=""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="")
                final_ans= final_ans + chunk.choices[0].delta.content


        # Display the question in a text field
        st.text_area('Questions Generated:', final_ans, height=500)

if __name__ == "__main__":
    main()







