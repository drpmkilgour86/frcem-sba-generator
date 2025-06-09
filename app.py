import streamlit as st
import openai
import os
from PyPDF2 import PdfReader

# Set your OpenAI API key here (replace with your actual key)
import os
openai.api_key = st.secrets["OPENAI_API_KEY"]


def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def build_prompt(topic, guideline_text, num_questions=1):
    return f"""
You are a consultant-level Emergency Medicine educator creating advanced SBA questions for the FRCEM Final SBA Exam (UK).

Instructions:
- Only use the information from the guideline below. Do not use general textbook knowledge.
- Avoid recall-style or fact-based questions.
- Questions should test complex clinical judgment, synthesis, or prioritisation.
- Choose less obvious, nuanced, or controversial areas from the guideline.
- Aim for high cognitive complexity (e.g., interpretation of findings, management prioritisation).
- Ensure distractors are:
    - Plausible
    - Internally consistent
    - Mutually exclusive
    - Equal in difficulty and tone to the correct answer
- All options should test the same conceptual level and not be obviously incorrect.
- Quote directly from the guideline to justify the correct answer after each explanation.
- Target difficulty: suitable for UK consultant-level candidates (e.g., FRCEM Final), aiming for facility index ~0.5.
- After each complete question + explanation, end with the line: ### ENDQUESTION ###

Guideline excerpt:
{guideline_text[:2000] if guideline_text else '[None provided]'}

Generate {num_questions} questions.
Format for each:
- Clinical stem
- Lead-in question
- 5 options (A–E)
- Correct answer
- Explanation (2–3 sentences)
- Quote directly from the guideline
"""

def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content

# Streamlit UI
# --- Streamlit App UI ---
st.title("FRCEM Final SBA Question Generator")
topic = st.text_input("Enter a curriculum topic:")
uploaded_file = st.file_uploader("Upload a relevant guideline (PDF only)", type="pdf")
num_questions = st.number_input("Number of questions", min_value=1, max_value=10, value=3)

# Track state
if "question_texts" not in st.session_state:
    st.session_state["question_texts"] = []
if "user_answers" not in st.session_state:
    st.session_state["user_answers"] = []
if "questions_displayed" not in st.session_state:
    st.session_state["questions_displayed"] = False

# Button: Generate Questions
if st.button("Generate Questions") and topic and uploaded_file:
    with st.spinner("Extracting guideline text and generating questions..."):
        guideline_text = extract_text_from_pdf(uploaded_file)
        full_text = generate_sba(topic, guideline_text, num_questions)
        question_blocks = full_text.strip().split("### ENDQUESTION ###")
        question_blocks = [q.strip() for q in question_blocks if q.strip()]
        st.session_state["question_texts"] = question_blocks
        st.session_state["user_answers"] = [None] * len(question_blocks)
        st.session_state["questions_displayed"] = True

# Display Questions
if st.session_state["questions_displayed"]:
    st.subheader("Generated Questions:")
    for i, block in enumerate(st.session_state["question_texts"]):
        if "Correct Answer:" in block:
            question_part = block.split("Correct Answer:")[0].strip()
            st.markdown(f"**Question {i+1}:**")
            st.markdown(question_part)
            st.session_state["user_answers"][i] = st.selectbox(
                f"Your answer to Question {i+1}",
                ["A", "B", "C", "D", "E"],
                key=f"answer_{i}"
            )

    if st.button("Submit Answers"):
        st.subheader("Answers and Explanations:")
        for i, block in enumerate(st.session_state["question_texts"]):
            st.markdown(f"**Question {i+1}**")
            st.markdown(block)
            st.markdown(f"**Your answer:** {st.session_state['user_answers'][i]}")
