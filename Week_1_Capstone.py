import streamlit as st
import dotenv
import openai
from groq import Groq
import os

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define AI personalities
system_prompts = {
    'Bot 1': 'You are Apple’s founder Steve Jobs. Respond to all questions as him, incorporating his mannerisms, knowledge of Apple, and his vision for the future. Keep responses within about 100 words and after every response, ask a question to the other bot which would escalate the debate.', 
    'Bot 2': 'You are American entrepreneur Elon Musk. Respond to all questions as him, incorporating his mannerisms, knowledge of Tesla and SpaceX, and his vision for the future. Keep responses within about 100 words and after every response, ask a question to the other bot which would escalate the debate.'
}

# Initialize Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "context" not in st.session_state:
    st.session_state.context = {"Bot 1": "", "Bot 2": ""}

oa_client = openai.OpenAI()

def get_bot_response(question: str, bot_type: str) -> str:
    """Fetches response from OpenAI (Bot 1) or Groq (Bot 2)."""
    try:
        model = "gpt-4o" if bot_type == "Bot 1" else "mixtral-8x7b-32768"
        system_content = system_prompts[bot_type]
        api_client = oa_client if bot_type == "Bot 1" else groq_client
        context = st.session_state.context[bot_type]

        if bot_type == "Bot 1":
            response = oa_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": f"Context: {context}\nQuestion: {question}"}
                ],
                temperature=0.7,
                max_tokens=150
            )
        else:
            response = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": f"Context: {context}\nQuestion: {question}"}
                ],
                temperature=0.7,
                max_tokens=150
            )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"

def judge_debate():
    if len(st.session_state.messages) == 0:
        st.warning("No debate history available for judgment.")
        return

    bot1_text = "\n".join([msg["content"] for msg in st.session_state.messages if msg["role"] == "Bot 1"])
    bot2_text = "\n".join([msg["content"] for msg in st.session_state.messages if msg["role"] == "Bot 2"])

    judge_prompt = f"""
    You are an imparunbiasedtial debate judge. Analyze the responses based on coherence, relevance, and depth of argumentation.

    Bot 1 (Steve Jobs) responses:
    {bot1_text}

    Bot 2 (Elon Musk) responses:
    {bot2_text}

    Declare the winner and explain in 3 lines why they won.

    Format:
    Winner: <Bot 1 or Bot 2>
    Explanation: <Three-line explanation>
    """

    try:
        response = oa_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an unbiased debate judge."},
                {"role": "user", "content": judge_prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )

        judgment = response.choices[0].message.content
        st.subheader("Judge Bot's Verdict")
        st.write(judgment)

    except openai.OpenAIError as e:
        st.error(f"An error occurred: {str(e)}")

def main():
    """Main function handling Streamlit UI and logic."""
    st.title("AI Debate: Steve Jobs vs. Elon Musk")
    st.write("This is a debate between AI versions of Steve Jobs and Elon Musk.")

    # Initial debate question
    question = "Who has contributed more to the greater advancement of Technology in society?"
    st.subheader(f"Debate Topic: {question}")

    # Only start the debate when the user clicks "Start Debate"
    if st.button("Start Debate"):
        st.session_state.messages = []  # Reset previous messages

        for i in range(25):  # Limit rounds to avoid excessive API calls
            role = "Bot 1"
            response = get_bot_response(question, role)
            st.session_state.messages.append({"role": role, "content": response})
            st.session_state.context[role] += response + " "
            question = get_bot_response(question, role)

            role = "Bot 2"
            response = get_bot_response(question, role)
            st.session_state.messages.append({"role": role, "content": response})
            st.session_state.context[role] += response + " "
            question = get_bot_response(question, role)

    # Display chat history in Streamlit UI
    if len(st.session_state.messages) > 0:
        st.subheader("Debate Transcript")
        with st.container():
            for message in st.session_state.messages:
                st.write(f"**{message['role']}:** {message['content']}")

    # Button to trigger the judge bot
    if st.button("Judge the Debate"):
        judge_debate()

if __name__ == "__main__":
    main()