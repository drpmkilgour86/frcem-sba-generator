import streamlit as st
import openai
from PyPDF2 import PdfReader

# Use OpenAI API key from Streamlit secrets
client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

# Extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Build prompt
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
- Target difficulty: suitable for UK consultant-level candidates (e.g., FRCEM Final)

Guideline excerpt:
{guideline_text[:2000] if guideline_text else '[None provided]'}

Format:
- Clinical stem
- A lead-in question
- 5 options (A–E)
- Correct Answer
- Explanation
"""

# Generate questions using GPT-4 Turbo
def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return ""

# Streamlit UI
st.title("FRCEM Final SBA Question Generator")

topic = st.text_input("Enter a curriculum topic:")
uploaded_file = st.file_uploader("Upload a relevant guideline (PDF only)", type="pdf")
num_questions = st.number_input("Number of questions", min_value=1, max_value=10, value=3)

if uploaded_file:
    guideline_text = extract_text_from_pdf(uploaded_file)
else:
    guideline_text = None

if st.button("Generate Questions") and topic and guideline_text:
    with st.spinner("Generating questions..."):
        questions = generate_sba(topic, guideline_text, num_questions)

    if questions:
        st.subheader("Generated Questions:")
        st.markdown(questions)
    else:
        st.warning("No questions were generated. Please check the topic and guideline.")
