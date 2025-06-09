
import streamlit as st
import openai
import os
import re
from PyPDF2 import PdfReader

# Use secrets for API key
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

Guideline excerpt:
{guideline_text[:2000] if guideline_text else '[None provided]'}

Format:
- Provide a clinical stem
- A lead-in question
- 5 options (A-E)
- Indicate the correct answer
- Provide a 2-3 sentence explanation
- Include a direct quote from the guideline supporting the correct answer
"""

def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    output = response.choices[0].message.content
    st.write("### ðŸ” DEBUG: Raw API Output")
    st.code(output)
    return output

# Streamlit UI
st.title("FRCEM Final SBA Question Generator")
topic = st.text_input("Enter a curriculum topic:")
uploaded_file = st.file_uploader("Upload a relevant guideline (PDF only)", type="pdf")
num_questions = st.number_input("Number of questions", min_value=1, max_value=10, value=3)

if st.button("Generate Questions") and topic and uploaded_file:
    with st.spinner("Extracting guideline text and generating questions..."):
        guideline_text = extract_text_from_pdf(uploaded_file)
        questions = generate_sba(topic, guideline_text, num_questions)

    st.subheader("Generated Questions:")
    question_blocks = re.split(r"\n\s*\n", questions.strip())

    if not question_blocks or len(question_blocks) < 1:
        st.warning("âš ï¸ No questions were returned from the model.")
        st.text_area("Raw model output:", questions, height=300)

    user_answers = []
    question_texts = []

    for i, block in enumerate(question_blocks):
        if "Correct Answer:" in block:
            split_block = block.split("Correct Answer:")
            question_part = split_block[0].strip()
            st.markdown(question_part)
            question_texts.append(block)
            options = ["A", "B", "C", "D", "E"]
            answer = st.selectbox(f"Your answer to Question {i+1}", options, key=f"answer_{i}")
            user_answers.append(answer)

    if len(question_texts) > 0 and st.button("Submit Answers"):
        st.subheader("Answers and Explanations:")
        for i, block in enumerate(question_texts):
            st.markdown(f"**Question {i+1}**")
            st.markdown(block)
            st.markdown(f"**Your answer:** {user_answers[i]}")
