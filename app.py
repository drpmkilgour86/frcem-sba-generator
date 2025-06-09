import streamlit as st
import openai
import os
from PyPDF2 import PdfReader

# Securely load your API key from Streamlit secrets
client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

# PDF text extraction
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Prompt builder for high-complexity FRCEM SBA questions
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

Format (for each of {num_questions} questions):
- Provide a clinical stem
- A lead-in question
- 5 options (A-E)
- Indicate the correct answer
- Provide a 2-3 sentence explanation
- Include a direct quote from the guideline supporting the correct answer
"""

# Generate questions using OpenAI
def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content

# Streamlit interface
st.title("FRCEM Final SBA Question Generator")
topic = st.text_input("Enter a curriculum topic:")
uploaded_file = st.file_uploader("Upload a relevant guideline (PDF only)", type="pdf")
num_questions = st.number_input("Number of questions", min_value=1, max_value=10, value=3)

if st.button("Generate Questions") and topic and uploaded_file:
    with st.spinner("Extracting guideline and generating questions..."):
        guideline_text = extract_text_from_pdf(uploaded_file)
        try:
            questions = generate_sba(topic, guideline_text, num_questions)
        except Exception as e:
            st.error(f"Error generating questions: {e}")
            st.stop()

    if not questions or "Correct Answer:" not in questions:
        st.warning("No valid questions were generated. Try another topic or guideline.")
        st.stop()

    st.subheader("Generated Questions:")
    raw_blocks = questions.strip().split("Correct Answer:")
    question_blocks = []

    for i in range(len(raw_blocks) - 1):
        block = raw_blocks[i].strip() + "\nCorrect Answer:" + raw_blocks[i + 1].strip().split("\n")[0]
        remainder = "\n".join(raw_blocks[i + 1].strip().split("\n")[1:])
        explanation = remainder.strip()
        question_blocks.append((block, explanation))

    user_answers = []

    for i, (question_text, explanation) in enumerate(question_blocks):
        st.markdown(f"**Question {i+1}**")
        st.markdown(question_text)
        answer = st.selectbox(f"Your answer to Question {i+1}", ["A", "B", "C", "D", "E"], key=f"answer_{i}")
        user_answers.append((answer, explanation))

    if st.button("Submit Answers"):
        st.subheader("Answers and Explanations:")
        for i, (user_answer, explanation) in enumerate(user_answers):
            st.markdown(f"**Question {i+1} – Your answer:** {user_answer}")
            st.markdown(f"**Explanation:** {explanation}")
