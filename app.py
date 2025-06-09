import streamlit as st
import openai
import os
from PyPDF2 import PdfReader

# Load API key securely from Streamlit secrets
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
- Use only the information from the guideline below (no general knowledge).
- Avoid recall-style or fact-based questions.
- Test complex clinical judgment, prioritisation, or synthesis.
- Choose nuanced or difficult guideline-based areas.
- Ensure all options are plausible, internally consistent, mutually exclusive, and equal in tone.
- Quote directly from the guideline to justify the correct answer.
- Use 5 options per question (A-E).
- Target high difficulty (FRCEM Final standard, facility index ~0.5).

Guideline excerpt:
{guideline_text[:2000] if guideline_text else '[None provided]'}

Format for each question:
- Clinical scenario (stem)
- Lead-in question
- 5 answer options (A–E)
- Indicate correct answer
- 2–3 sentence explanation
- Include supporting quote from the guideline

Example of a poor question (too easy or unbalanced):
Clinical Scenario: A 42-year-old marathon runner collapses immediately after finishing a race. On arrival of the emergency medical team, the patient is unresponsive, apneic, and pulseless...
Correct Answer: C
Explanation: ...

Example of a well-constructed, challenging question:
A 90-year-old woman complains of neck pain and limb weakness following a fall onto her face...
Correct Answer: A
Explanation: ...
"""

def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content

# Streamlit App
st.title("FRCEM Final SBA Question Generator")

topic = st.text_input("Enter a curriculum topic:")
uploaded_file = st.file_uploader("Upload a relevant guideline (PDF only)", type="pdf")
num_questions = st.number_input("Number of questions", min_value=1, max_value=10, value=3)

if st.button("Generate Questions") and topic and uploaded_file:
    with st.spinner("Generating questions..."):
        guideline_text = extract_text_from_pdf(uploaded_file)
        questions = generate_sba(topic, guideline_text, num_questions)

    st.subheader("Generated Questions:")

    # Split each question block before "Correct Answer"
    question_blocks = questions.split("Correct Answer:")
    user_answers = []
    reconstructed_blocks = []

    if len(question_blocks) <= 1:
        st.error("No questions were generated. Please check the guideline or try again.")
    else:
        for i in range(len(question_blocks) - 1):
            full_question = question_blocks[i].strip() + "\n\nCorrect Answer:" + question_blocks[i + 1].split("\n")[0].strip()
            reconstructed_blocks.append(full_question)

        for i, block in enumerate(reconstructed_blocks):
            lines = block.strip().split("\n")
            visible_part = "\n".join([line for line in lines if not line.startswith("Correct Answer:")])
            st.markdown(f"**Question {i+1}**")
            st.markdown(visible_part)
            options = ["A", "B", "C", "D", "E"]
            user_choice = st.selectbox(f"Your answer to Question {i+1}", options, key=f"q_{i}")
            user_answers.append(user_choice)

        if st.button("Submit Answers"):
            st.subheader("Answers and Explanations:")
            for i, block in enumerate(reconstructed_blocks):
                st.markdown(f"**Question {i+1}**")
                st.markdown(block)
                st.markdown(f"**Your answer:** {user_answers[i]}")
