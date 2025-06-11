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

# UPDATED build_prompt with uniqueness instruction
def build_prompt(topic, guideline_text, num_questions=1):
    return f"""
You are a consultant-level Emergency Medicine educator creating advanced Single Best Answer (SBA) questions for the FRCEM Final SBA Exam (UK).

Instructions:
- Generate **exactly {num_questions} distinct questions**.
- Each question must be **materially different** from the others in clinical focus and reasoning.
    - For example, if Question 1 is about sedation with IM ketamine in acute behavioural disturbance (ABD), do **not** reuse IM ketamine as a correct answer in the other questions.
    - Instead, focus on **different aspects** of the topic (e.g., oral sedation, symptom recognition, risk factors, de-escalation techniques).
- Base all questions **only** on the content from the uploaded guideline below. Do **not** use general textbook knowledge.
- Do **not** generate recall-style questions (e.g., definitions or memorised facts).
- Use **British English healthcare terminology** (e.g., "ED", "A+E", "resuscitation room", "paracetamol"), not American terms (e.g., "ER", "acetaminophen").
- Questions must assess **clinical judgment**, **interpretation**, or **management decisions**, not superficial recall.
- To increase difficulty:
    - Give **clues to the diagnosis in the clinical stem**, but do **not** name the diagnosis directly.
    - Candidates should have to **infer the diagnosis** and then apply clinical reasoning to select the correct option.
- Use **specific numerical values** (e.g., HR, Na+, BP) in stems rather than vague terms like “high” or “low”.
    - Ensure values are **internally consistent** (e.g., if the question is about AF with fast ventricular response, heart rate should be >120 bpm).
- Avoid giveaway phrases like “as per the guideline recommendation” in any answer option.
- Ensure all answer choices are:
    - Plausible
    - Internally consistent (e.g., do **not** offer “prostatitis” in a question about LUTS in a female)
    - Mutually exclusive
    - Equal in complexity and tone
    - Sufficiently challenging to a senior Emergency Medicine trainee
- Difficulty target: suitable for UK consultant-level candidates (FRCEM Final SBA), aiming for a facility index ~0.5.

Guideline excerpt:
{guideline_text[:2000] if guideline_text else '[None provided]'}

Each question must follow this format:
- Clinical scenario (stem)
- Lead-in question
- 5 answer options (A–E)
- Indicate the correct answer
- Provide a 2–3 sentence explanation
- Include a **direct quote** from the guideline supporting the correct answer

✅ Example of a well-constructed question and why it is effective:

A 90-year-old woman complains of neck pain and limb weakness following a fall from standing on to the face. A CT-scan of the cervical spine shows only degenerative changes with no fracture.

Which of the following examination findings is most associated with the spinal cord syndrome likely caused by this fall?

A) Hyperesthesia of the arms  
B) Bilateral flaccid paralysis of all limbs  
C) Decreased peri-anal sensation  
D) Bilateral sensory loss of all limbs  
E) Decreased proprioception and vibration sense in the lower limbs

Correct Answer: A

Why this is effective:
The stem gives enough detail to infer central cord syndrome without naming it. The candidate must recognise the pattern and apply judgment. Distractors are plausible and internally consistent.

❌ Poor example 1: Too easy

A 38-year-old man is brought to ED by police after erratic behaviour. He is highly agitated and requires restraint.

What is the next step?

A. Call security  
B. Give oral lorazepam  
C. Give IM ketamine or droperidol  
D. Wait for psychiatry  
E. Move to a quieter area

Correct Answer: C

Why it's poor: Options are not equally plausible. The answer is obvious. No reasoning is required.

❌ Poor example 2: Giveaway language

A 42-year-old woman with bipolar disorder is restrained and remains highly agitated.

Which drug should be used?

A. Oral haloperidol  
B. IV diazepam  
C. IM droperidol **as per the guideline recommendation**  
D. Oral risperidone  
E. Await psychiatry

Correct Answer: C

Why it’s poor: The correct option is clearly flagged by wording. This reduces the validity of the question.

Avoid these issues in all generated questions.
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
