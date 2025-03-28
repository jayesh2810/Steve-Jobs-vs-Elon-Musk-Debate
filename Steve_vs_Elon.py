import streamlit as st
import dotenv
import os
import time
from groq import Groq

dotenv.load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define AI personalities
system_prompts = {
    'Steve Jobs': (
        "You are Apple’s founder Steve Jobs. Respond to all questions as him, "
        "incorporating his mannerisms, knowledge of Apple, and his vision for the future. "
        "Keep responses within about 100 words and after every response, ask a question to the other bot which would escalate the debate."
    ),
    'Elon Musk': (
        "You are American entrepreneur Elon Musk. Respond to all questions as him, "
        "incorporating his mannerisms, knowledge of Tesla and SpaceX, and his vision for the future. "
        "Keep responses within about 100 words and after every response, ask a question to the other bot which would escalate the debate."
    )
}

# Initialize Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = {"Steve Jobs": "", "Elon Musk": ""}

def get_bot_response(question: str, bot_type: str) -> str:
    """Fetches response from Groq API using LLaMA 3.3-70B model."""
    try:
        model = "llama-3.3-70b-versatile"
        system_content = system_prompts[bot_type]
        context = st.session_state.context[bot_type]
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

def typewriter_effect(text, display_area):
    """Displays text one word at a time for a typewriter effect."""
    words = text.split()
    displayed_text = ""
    for word in words:
        displayed_text += word + " "
        display_area.write(displayed_text)
        time.sleep(0.1)

def judge_debate():
    """Evaluates and judges the debate."""
    if len(st.session_state.messages) == 0:
        st.warning("No debate history available for judgment.")
        return

    steve_text = "\n".join([msg["content"] for msg in st.session_state.messages if msg["role"] == "Steve Jobs"])
    elon_text = "\n".join([msg["content"] for msg in st.session_state.messages if msg["role"] == "Elon Musk"])

    judge_prompt = f"""
    You are an unbiased debate judge. Analyze the responses based on coherence, relevance, and depth of argumentation.

    Steve Jobs' responses:
    {steve_text}

    Elon Musk's responses:
    {elon_text}

    Declare the winner and explain in 3 lines why they won.

    Format:
    Winner: <Steve Jobs or Elon Musk>
    Explanation: <Three-line explanation>
    """

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

def main():
    """Main function handling Streamlit UI and logic."""
    st.title("AI Debate: Steve Jobs vs. Elon Musk")
    st.write("This is a debate between AI versions of Steve Jobs and Elon Musk.")

    # Initial debate question
    question = "Who has contributed more to the greater advancement of technology in society?"
    st.subheader(f"Debate Topic: {question}")

    if st.button("Start Debate"):
        st.session_state.messages = []
        st.session_state.context = {"Steve Jobs": "", "Elon Musk": ""}
        last_speaker = None  # To track the last bot that responded

        rounds = 3  # Number of debate rounds
        for i in range(rounds):
            # Steve Jobs responds
            role = "Steve Jobs"
            response = get_bot_response(question, role)
            st.session_state.messages.append({"role": role, "content": response})
            st.session_state.context[role] += response + " "
            last_speaker = role  # Update last speaker
            st.subheader(f"**{role}:**")
            display_area = st.empty()
            typewriter_effect(response, display_area)
            
            question = response

            # Elon Musk responds
            role = "Elon Musk"
            response = get_bot_response(question, role)
            st.session_state.messages.append({"role": role, "content": response})
            st.session_state.context[role] += response + " "
            last_speaker = role  # Update last speaker
            st.subheader(f"**{role}:**")
            display_area = st.empty()
            typewriter_effect(response, display_area)
            
            question = response

        # After the debate rounds, determine which bot must provide the closing statement.
        if last_speaker == "Steve Jobs":
            final_role = "Elon Musk"
            final_prompt = (
                "Steve Jobs posed a final question. "
                "Please provide your closing statement that summarizes your position and includes no further questions to conclude the debate."
            )
        elif last_speaker == "Elon Musk":
            final_role = "Steve Jobs"
            final_prompt = (
                "Elon Musk posed a final question. "
                "Please provide your closing statement that summarizes your position and includes no further questions to conclude the debate."
            )
        else:
            final_role = None

        if final_role:
            final_response = get_bot_response(final_prompt, final_role)
            st.session_state.messages.append({"role": final_role, "content": final_response})
            st.session_state.context[final_role] += final_response + " "
            st.subheader(f"**{final_role}:**")
            display_area = st.empty()
            typewriter_effect(final_response, display_area)

    # Display the complete debate transcript
    if st.session_state.messages:
        st.subheader("Debate Transcript")
        with st.container():
            for message in st.session_state.messages:
                st.write(f"**{message['role']}:** {message['content']}")

    # Button to trigger the judge bot
    if st.button("Judge the Debate"):
        judge_debate()

if __name__ == "__main__":
    main()
