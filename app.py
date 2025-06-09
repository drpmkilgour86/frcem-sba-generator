import streamlit as st
from PyPDF2 import PdfReader
import openai

# Use OpenAI API key from Streamlit secrets
client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

# Function to extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Function to build the prompt
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
- Do not display the correct answer or explanation until the user has submitted their response.

Guideline excerpt:
{guideline_text[:2000] if guideline_text else '[None provided]'}

Format for each question:
- Clinical stem
- A lead-in question
- 5 options (A-E)
- “Correct Answer: X”
- “Explanation: ...”
"""

# Function to generate SBA questions
def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        full_output = response.choices[0].message.content.strip()
        blocks = full_output.split("\n\n")
        valid_blocks = [b for b in blocks if "Correct Answer:" in b and "Explanation:" in b]
        return valid_blocks
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []

# Streamlit UI
st.title("FRCEM Final SBA Question Generator")

topic = st.text_input("Enter a curriculum topic:")
uploaded_file = st.file_uploader("Upload a relevant guideline (PDF only)", type="pdf")
num_questions = st.number_input("Number of questions", min_value=1, max_value=10, value=3)

if "guideline_text" not in st.session_state:
    st.session_state.guideline_text = None

if uploaded_file:
    st.session_state.guideline_text = extract_text_from_pdf(uploaded_file)

if st.button("Generate Questions") and topic and st.session_state.guideline_text:
    with st.spinner("Generating questions..."):
        questions = generate_sba(topic, st.session_state.guideline_text, num_questions)
    st.session_state.questions = questions
    st.session_state.answers_submitted = False

if "questions" in st.session_state and st.session_state.questions:
    st.subheader("Generated Questions:")
    user_answers = []
    question_texts = []

    for i, block in enumerate(st.session_state.questions):
        split_block = block.split("Correct Answer:")
        if len(split_block) < 2:
            continue
        question_part = split_block[0].strip()
        st.markdown(f"**Question {i+1}**")
        st.markdown(question_part)
        options = ["A", "B", "C", "D", "E"]
        answer = st.selectbox(f"Your answer to Question {i+1}", options, key=f"answer_{i}")
        user_answers.append(answer)
        question_texts.append(block)

    if st.button("Submit Answers"):
        st.session_state.answers_submitted = True
        st.session_state.user_answers = user_answers

if st.session_state.get("answers_submitted"):
    st.subheader("Answers and Explanations:")
    for i, block in enumerate(st.session_state.questions):
        st.markdown(f"**Question {i+1}**")
        st.markdown(block)
        st.markdown(f"**Your answer:** {st.session_state.user_answers[i]}")
