import streamlit as st
import openai
import os
from PyPDF2 import PdfReader

# Authenticate with OpenAI using Streamlit secrets
client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

# Extract text from uploaded guideline
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    return "".join(page.extract_text() or "" for page in reader.pages)

# Build the AI prompt
def build_prompt(topic, guideline_text, num_questions=1):
    return f"""
You are a consultant-level Emergency Medicine educator creating advanced SBA questions for the FRCEM Final SBA Exam (UK).

Instructions:
- Only use the information from the guideline below. Do not use general textbook knowledge.
- Avoid recall-style or fact-based questions.
- Choose less obvious, nuanced, or controversial areas from the guideline.
- Ensure distractors are plausible, internally consistent, mutually exclusive, and all plausible.
- All options should test the same conceptual level.
- Quote directly from the guideline to justify the correct answer.

Guideline excerpt:
{guideline_text[:2000]}

Generate {num_questions} questions. Format each like:
Clinical Scenario:
Lead-in Question:
A. Option
B. Option
C. Option
D. Option
E. Option
Correct Answer: [Letter]
Explanation: [Short explanation]
Guideline Quote: [Exact quote from the PDF]
"""

# Generate SBA questions from prompt
def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content

# Streamlit app layout
st.title("FRCEM Final SBA Question Generator")

# Topic input
topic = st.text_input("Enter a curriculum topic:")

# File uploader
uploaded_file = st.file_uploader("Upload a relevant guideline (PDF only)", type="pdf")

# Retain extracted guideline text
if uploaded_file:
    st.session_state["guideline_text"] = extract_text_from_pdf(uploaded_file)

# Number of questions
num_questions = st.number_input("Number of questions", min_value=1, max_value=10, value=3)

# Generate button
if st.button("Generate Questions") and topic and "guideline_text" in st.session_state:
    with st.spinner("Generating questions..."):
        questions = generate_sba(topic, st.session_state["guideline_text"], num_questions)
        st.session_state["questions"] = questions

# Display questions only if they exist
if "questions" in st.session_state:
    st.subheader("Generated Questions:")
    question_blocks = st.session_state["questions"].strip().split("\n\n")

    user_answers = []
    question_texts = []

    for i, block in enumerate(question_blocks):
        if "Correct Answer:" in block:
            question_part = block.split("Correct Answer:")[0].strip()
            st.markdown(f"**Question {i+1}**")
            st.markdown(question_part)
            options = ["A", "B", "C", "D", "E"]
            answer = st.selectbox(f"Your answer to Question {i+1}", options, key=f"answer_{i}")
            user_answers.append(answer)
            question_texts.append(block)

    if st.button("Submit Answers"):
        st.subheader("Answers and Explanations:")
        for i, block in enumerate(question_texts):
            st.markdown(f"**Question {i+1}**")
            st.markdown(block)
            st.markdown(f"**Your answer:** {user_answers[i]}")
