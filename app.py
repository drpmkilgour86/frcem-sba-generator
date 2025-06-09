
import streamlit as st
from PyPDF2 import PdfReader
import openai
import os

# Initialize OpenAI client using the modern SDK and Streamlit secrets
client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

st.set_page_config(page_title="FRCEM Final SBA Generator", layout="wide")
st.title("FRCEM Final SBA Question Generator")

@st.cache_data
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def build_prompt(topic, guideline_text, num_questions=1):
    return f'''
You are a consultant-level Emergency Medicine educator creating advanced SBA questions for the FRCEM Final SBA Exam (UK).

Instructions:
- Use ONLY the information in the guideline provided below.
- Avoid recall-style or basic questions.
- Focus on complex clinical decision-making, synthesis, and prioritization.
- Choose less obvious, nuanced, or controversial areas from the guideline.
- Target difficulty: consultant-level UK EM (FRCEM Final), facility index ~0.5.
- Ensure options are plausible, mutually exclusive, and consistent in tone.
- Each question must contain:
    - Clinical stem
    - Lead-in question
    - 5 options (A-E)
    - Correct answer
    - 2â€“3 sentence explanation
    - Direct quote from the guideline justifying the correct answer

Guideline excerpt:
{guideline_text[:2000]}

Output {num_questions} questions in the format specified above.
'''

def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content

# Persistent session state for uploaded text
if "guideline_text" not in st.session_state:
    st.session_state["guideline_text"] = None

topic = st.text_input("Enter a curriculum topic:")
uploaded_file = st.file_uploader("Upload a relevant guideline (PDF only)", type="pdf")

if uploaded_file:
    st.session_state["guideline_text"] = extract_text_from_pdf(uploaded_file)

num_questions = st.number_input("Number of questions", min_value=1, max_value=5, value=1)

if st.button("Generate Questions") and topic and st.session_state["guideline_text"]:
    with st.spinner("Generating high-quality FRCEM questions..."):
        try:
            questions_raw = generate_sba(topic, st.session_state["guideline_text"], num_questions)
            st.session_state["questions"] = [
                q.strip() for q in questions_raw.split("\n\n") if "Correct Answer:" in q
            ]
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.stop()

if "questions" in st.session_state and st.session_state["questions"]:
    st.subheader("Generated Questions:")
    answers = []
    for idx, q_block in enumerate(st.session_state["questions"]):
        question_part = q_block.split("Correct Answer:")[0].strip()
        st.markdown(f"**Question {idx + 1}**")
        st.markdown(question_part)
        user_choice = st.selectbox(f"Your answer to Question {idx + 1}:", ["A", "B", "C", "D", "E"], key=f"ans_{idx}")
        answers.append((q_block, user_choice))

    if st.button("Submit"):
        st.subheader("Answers and Explanations:")
        for idx, (block, user_answer) in enumerate(answers):
            st.markdown(f"**Question {idx + 1}**")
            st.markdown(block)
            st.markdown(f"**Your answer:** {user_answer}")
