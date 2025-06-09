import streamlit as st
import openai
import os
from PyPDF2 import PdfReader

# Load API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Function to extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Prompt template for GPT
def build_prompt(topic, guideline_text, num_questions=1):
    return f"""
You are a consultant-level Emergency Medicine educator creating advanced SBA questions for the FRCEM Final SBA Exam (UK).

Instructions:
- Only use the information from the uploaded guideline below.
- Avoid recall-style or fact-based questions.
- Focus on complex clinical judgment, interpretation, and prioritisation.
- Emphasise niche, less obvious aspects of the guideline over core textbook knowledge.
- Ensure all options are:
    - Plausible
    - Internally consistent
    - Mutually exclusive
    - Equal in tone and difficulty
- Avoid making the correct answer obviously stand out.
- Quote directly from the guideline to justify the correct answer after each explanation.
- Target difficulty: UK consultant level (FRCEM), aiming for borderline performance (facility index ~0.5).

Uploaded Guideline Excerpt:
{guideline_text[:2000] if guideline_text else '[None provided]'}

Format for each question:
- Clinical stem
- Lead-in question
- Five answer options (A–E)
- Clearly marked correct answer
- 2–3 sentence explanation
- Include a supporting quote from the guideline

Example of a well-crafted, difficult question:
A 90-year-old woman complains of neck pain and limb weakness following a fall from standing on to the face. A CT-scan of the cervical spine shows only degenerative changes with no fracture.

Which of the following examination findings is most associated with the spinal cord syndrome likely caused by this fall?

A: Hyperesthesia of the arms
B: Bilateral flaccid paralysis of all limbs
C: Decreased peri-anal sensation
D: Bilateral sensory loss of all limbs
E: Decreased proprioception and vibration sense in the lower limbs

Correct Answer: A
Explanation: This presentation is consistent with central cord syndrome, typically seen after hyperextension in elderly patients with cervical spondylosis. Upper limbs are affected more than lower limbs.
"""

# Function to generate SBA questions using OpenAI API
def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content

# Streamlit UI
st.title("FRCEM Final SBA Question Generator")

topic = st.text_input("Enter a curriculum topic:")
uploaded_file = st.file_uploader("Upload a relevant clinical guideline (PDF only)", type="pdf")
num_questions = st.number_input("Number of questions to generate", min_value=1, max_value=10, value=3)

if st.button("Generate Questions") and topic and uploaded_file:
    with st.spinner("Generating SBA questions from the uploaded guideline..."):
        guideline_text = extract_text_from_pdf(uploaded_file)
        questions = generate_sba(topic, guideline_text, num_questions)

    st.subheader("Questions to Answer:")
    question_blocks = questions.strip().split("\n\n")
    user_answers = []
    question_texts = []

    for i, block in enumerate(question_blocks):
        if "Correct Answer:" in block:
            question_part = block.split("Correct Answer:")[0].strip()
            st.markdown(f"**Question {i+1}:**")
            st.markdown(question_part)
            question_texts.append(block)
            answer = st.selectbox(f"Your answer to Question {i+1}", ["A", "B", "C", "D", "E"], key=f"answer_{i}")
            user_answers.append(answer)

    if st.button("Submit Answers"):
        st.subheader("Answers and Explanations:")
        for i, block in enumerate(question_texts):
            st.markdown(f"**Question {i+1}:**")
            st.markdown(block)
            st.markdown(f"**Your answer:** {user_answers[i]}")
