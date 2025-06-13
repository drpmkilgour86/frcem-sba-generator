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

# FINAL UPDATED build_prompt
def build_prompt(topic, guideline_text, num_questions=1):
    return f"""  
You are a consultant-level Emergency Medicine educator creating advanced Single Best Answer (SBA) questions for the FRCEM Final SBA examination. You will be provided with text from a clinical guideline and a topic area. Your task is to generate high-quality exam-style questions that are realistic, varied, and directly based on the content of the guideline.

You must generate **exactly {num_questions} SBA questions** that meet the criteria below.

Each question should:
- Be written in the style of the FRCEM Final SBA exam.
- Include a realistic clinical stem based on Emergency Department presentations.
- Avoid explicitly naming the diagnosis in the stem — instead, present findings that require interpretation.
- Contain a one-sentence lead-in question that clearly asks for a single best answer.
- Include exactly 5 answer options labelled A to E, with only one clearly best answer.
- Provide the correct answer and a brief explanation that references the guideline text provided.
- Be materially different from previous questions in the same set. For example, if the first question on acute behavioural disturbance is about sedation with ketamine, later questions should focus on other aspects (e.g., oral sedation, symptoms, or legal considerations).
- Avoid using the same correct answer repeatedly across a question set.
- Use UK-based terminology and guidelines.
- Focus on applied clinical decision-making rather than recall of isolated facts.
- Ensure distractors are all plausible and represent realistic differential diagnoses or common pitfalls.
- Vary the question type across a set: include diagnosis, immediate management, risk stratification, complication recognition, and ethical/legal reasoning.
- Include relevant test results (e.g., bloods, imaging, vitals) when appropriate to support clinical reasoning.

Additional instructions to improve quality:
- Avoid using ‘All of the above’ or ‘None of the above’ as answer options.
- Avoid referencing specific guideline names (e.g., NICE, SIGN) or tools (e.g., GRACE, Decision Support Tool) in the stem or lead-in. Instead, reflect their recommendations in the explanation.
- Avoid including actions that fall outside the scope of Emergency Medicine (e.g., initiating biologic therapy or detaining under the Mental Health Act). If relevant, test knowledge of appropriate referral pathways.
- Ensure the correct answer represents a decision that an ED doctor could reasonably take in the emergency setting.
- Each distractor should be independently plausible or incorrect — do not rely on trick formats or obviously irrelevant choices.
    - For example, do not list “prostatitis” as an answer option in a question about a female with urinary symptoms.

Important constraints:
- All clinical scenarios must take place in a realistic Emergency Department context in the UK.
- Only include procedures or decisions that would occur in the ED, not in theatre or elective settings.
- Base all medical management decisions (e.g., drug choice, dosage, order of actions) strictly on what is in the guideline. Do not invent treatments not mentioned.
- If the guideline does not contain sufficient information to support a safe and realistic question on a topic, do not make up details. Instead, skip that question.

Internal planning steps:
Step 1: Read the guideline and identify 3–5 key clinical decision points or themes that can be assessed.
Step 2: For each question, select a different concept or decision point as its focus.
Step 3: Ensure each question tests a different aspect of clinical reasoning or guideline application.

Example of strong variation across questions from a sedation guideline:
Q1: What is the first-line sedative for rapid tranquillisation in ABD?
Q2: What observations should be performed immediately after IM sedation?
Q3: What is the legal framework required before sedating a patient without capacity?
Q4: Which factors increase the risk of respiratory depression following sedation?

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

Now generate {num_questions} SBA question(s) on the topic: {topic}
The relevant guideline text is below:
\"\"\"{guideline_text}\"\"\"
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
