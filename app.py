import streamlit as st
import openai
from PyPDF2 import PdfReader

# Use OpenAI API key stored securely in Streamlit secrets
openai.api_key = st.secrets["openai_api_key"]

# Extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Build prompt to send to GPT
def build_prompt(topic, guideline_text, num_questions=1):
    return f"""
You are a consultant-level Emergency Medicine educator creating advanced Single Best Answer (SBA) questions for the FRCEM Final SBA Exam (UK).

Instructions:
- Only use the content from the uploaded guideline below. Do not use general textbook knowledge.
- Do not generate recall-style questions (e.g., simple factual statements or definitions).
- Avoid American healthcare terminology. Use British English (e.g., "A+E" or "ED", not "ER").
- Ensure questions reflect the level of clinical reasoning expected of UK Emergency Medicine consultants.
- Focus on applying, synthesising, or interpreting complex clinical data.
- Avoid obvious answers. Distractors must be plausible, internally consistent, and test the same conceptual level.

Guideline excerpt:
{guideline_text[:2000] if guideline_text else '[None provided]'}

Each question must follow this format:
- Clinical scenario (stem)
- Lead-in question
- 5 answer options (A–E)
- Indicate the correct answer
- Provide a 2–3 sentence explanation
- Include a direct quote from the guideline supporting the answer

Example of a well-constructed question and why it is effective:

A 90-year-old woman complains of neck pain and limb weakness following a fall from standing on to the face. A CT-scan of the cervical spine shows only degenerative changes with no fracture.

Which of the following examination findings is most associated with the spinal cord syndrome likely caused by this fall?

A) Hyperesthesia of the arms  
B) Bilateral flaccid paralysis of all limbs  
C) Decreased peri-anal sensation  
D) Bilateral sensory loss of all limbs  
E) Decreased proprioception and vibration sense in the lower limbs

Correct Answer: A

Explanation: This question requires clinical reasoning — the candidate must:
- Recognise the likely diagnosis (central cord syndrome),
- Apply knowledge of typical clinical features,
- Navigate plausible distractors that represent other spinal syndromes.
This avoids simple fact recall and instead mirrors consultant-level decision-making in Emergency Medicine.

Example of a poorly constructed question and why it is not effective:

Clinical Scenario:  
A 38-year-old man is brought into the Emergency Department (ED) by police, following reports of erratic behavior and aggression at a local shopping center. On arrival, he is vocal, sweating profusely, and displaying significant physical agitation. Attempts at verbal de-escalation have been unsuccessful and you are concerned about his safety and that of others around him. There is a significant sustained physical effort in restraining him, showing no signs of calming down.

Lead-in Question:  
What is the most appropriate next step in the management of this patient's acute behavioral disturbance?

A. Request immediate assistance from hospital security personnel  
B. Administer oral lorazepam for sedation  
C. Prepare for parenteral sedation with intramuscular ketamine or droperidol  
D. Move the patient to a quieter area of the ED to continue attempts at verbal de-escalation  
E. Wait for psychiatric assessment before any further intervention

Correct Answer: C

Why this is a poor question: While the scenario is relevant, the distractors are too basic and clearly inferior to the correct answer. Most trainees would easily eliminate all but one choice without requiring nuanced clinical reasoning. The question does not adequately test synthesis or decision-making beyond surface-level knowledge.
"""

# Generate SBA questions using OpenAI API
def generate_sba(topic, guideline_text, num_questions=1):
    prompt = build_prompt(topic, guideline_text, num_questions)
    try:
        response = openai.ChatCompletion.create(
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
