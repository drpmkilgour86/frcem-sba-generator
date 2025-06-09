import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI

# Set up the OpenAI client using the new SDK (v1.0+)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
- 5 options (A–E)
- Indicate the correct answer
- Provide a 2–3 sentence explanation
- Include a direct quote from the guideline supporting the correct answer

Example of a poorly balanced question:
Clinical Scenario: A 42-year-old marathon runner collapses immediately after finishing a race. On arrival of the emergency medical team, the patient is unresponsive, apneic, and pulseless. Cardiopulmonary resuscitation (CPR) is initiated, and an Automated External Defibrillator (AED) is applied, which advises no shock. The medical history includes no known allergies or cardiac problems.

Lead-in Question: Considering the 2021 Special Circumstances Guidelines, which of the following is the most appropriate next step in the management of this patient?

A. Administer high-dose epinephrine immediately for potential anaphylaxis
B. Initiate targeted temperature management (TTM) at 32–36°C
C. Perform a focused assessment for potential reversible causes, including the 4 H’s and 4 T’s
D. Transport to the nearest hospital without further on-scene intervention
E. Administer 1.0 mg of intravenous adrenaline as part of standard ACLS protocol

Correct Answer: C
Explanation: The scenario describes a sudden collapse post-exercise. The 2021 Special Circumstances Guidelines emphasize identifying reversible causes using the 4 H’s and 4 T’s. This takes precedence before assuming cardiac or anaphylactic causes.

Example of a well-crafted, difficult question:
A 90-year-old woman complains of neck pain and limb weakness following a fall from standing on to the face. A CT-scan of the cervical spine shows only degenerative changes with no fracture.

Which of the following examination findings is most associated with the spinal cord syndrome likely caused by this fall?

A: Hyperesthesia of the arms  
B: Bilateral flaccid paralysis of all limbs  
C: Decreased peri-anal sensation  
D: Bilateral sensory loss of all limbs  
E: Decreased proprioception and vibration sense in the lower limbs

Correct Answer: A  
Explanation: This presentation is consistent with central cord syndrome, which is classically associated with hyperextension injuries in elderly patients with cervical spondylosis. It disproportionately affects the upper limbs, often presenting with hyperesthesia or weakness in the arms more than the legs.
"""

def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content

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
    question_blocks = questions.strip().split("\n\n")

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

    if st.button("Submit Answers"):
        st.subheader("Answers and Explanations:")
        for i, block in enumerate(question_texts):
            st.markdown(f"**Question {i+1}**")
            st.markdown(block)
            st.markdown(f"**Your answer:** {user_answers[i]}")
