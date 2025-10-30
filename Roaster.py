import streamlit as st
import fitz  # PyMuPDF
import requests
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# === PASTE YOUR API KEY HERE (ONCE) ===
OPENROUTER_API_KEY = "ENTER YOU API KEY"  # ← YOUR KEY

# === API SETUP ===
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "http://localhost:8501",
    "X-Title": "ResumeRoaster",
    "Content-Type": "application/json",
}

# --- DEEPSEEK R1T2 CHIMERA CALL (FREE TIER) ---
def qwen_3(prompt, system_msg, max_tokens=200, temperature=0.9):
    if not OPENROUTER_API_KEY:
        return "API Key missing. Get free at openrouter.ai/keys"

    data = {
        "model": "google/gemini-2.0-flash-exp:free",  # Your beast
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            return f"API Error {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return f"Request failed: {str(e)}"


# --- PDF TO TEXT (KEEPS IT CLEAN) ---
def pdf_to_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()[:3000]  # Cap for API limits


# --- ROAST PROMPT (SAVAGE MODE) ---
def generate_roast(resume_text):
    prompt = f"""
You are a merciless, hyper-articulate resume assassin — a mix of Gordon Ramsay, Wednesday Addams, and a burnt-out HR veteran 
who’s reviewed too many “results-driven team players.” 

Your mission: Annihilate this resume with savage precision, dark humor, and articulate brutality. 
Mock clichés, buzzwords, and empty achievements like they insulted your intelligence. 
Use language that’s funny, creative, and lethal — sharp enough to make them rethink their life choices. 
Keep it under 150 words. End with ONE helpful tip (like a shard of mercy after the chaos).

Example tones to emulate:
- “This resume radiates the same energy as a PowerPoint from 2007 and a cry for help.”
- “If buzzwords were achievements, this person would be a CEO by now.”
- “Reading this felt like being trapped in an elevator with a motivational speaker and no escape.”

Now roast the following resume at ☢️ NUCLEAR DETONATION LEVEL ☢️:

Resume:
{resume_text}

Roast:
"""
    system = (
        "You are a brutally witty AI resume roaster — eloquent, darkly funny, and unforgiving. "
        "Deliver savage yet intelligent humor that exposes every flaw but ends with one constructive tip. "
        "Keep your tone confident, vicious, and clever — think Shakespeare with a grudge."
    )
    return qwen_3(prompt, system, max_tokens=150, temperature=0.95)



# --- REWRITE PROMPT (ATS KILLER) ---
def rewrite_resume(resume_text):
    prompt = f"""Rewrite this resume for ATS success and recruiter wow-factor. Use action verbs (led, optimized), quantifiable wins (increased 30%), keywords (Python, ML, AWS, Agile). Structure: Sections with bullets. Keep original length.

Original: {resume_text}

Optimized Resume:"""
    system = "You are a top recruiter. Make it scannable, keyword-rich, achievement-focused. Professional tone."
    return qwen_3(prompt, system, max_tokens=400, temperature=0.3)

# --- PDF CREATOR (PRO-LEVEL) ---
def create_pdf(content, title):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 14)
    c.drawString(80, height - 80, title)
    c.setFont("Helvetica", 11)
    y = height - 110
    lines = content.split("\n") if content else ["No content."]
    for line in lines:
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(80, y, line[:85])
        y -= 14
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# === CLEAN UI ===
st.set_page_config(page_title="ResumeRoaster", layout="wide")
st.title("🔥 ResumeRoaster")
st.markdown("**Upload → See roast → Download fixed ATS resume**")

if "PASTE_YOUR_REAL_KEY_HERE" in OPENROUTER_API_KEY:
    st.error("PASTE YOUR API KEY ON LINE 9!")
    st.stop()

file = st.file_uploader("Upload Resume (PDF)", type="pdf")

if file:
    with st.spinner("Processing..."):
        text = pdf_to_text(file)
        if len(text) < 50:
            st.error("Resume too short!")
            st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔥 ROAST")
        roast = generate_roast(text)
        st.text_area("", value=roast, height=300, key="roast", label_visibility="collapsed")

    with col2:
        st.subheader("✅ ATS REWRITE")
        rewrite = rewrite_resume(text)
        st.text_area("", value=rewrite, height=300, key="rewrite", label_visibility="collapsed")

    score = min(100, len(rewrite.split()) * 0.5 + 30)
    st.metric("Hire Score", f"{int(score)}/100")

    # ONLY ONE DOWNLOAD: ATS PDF
    st.markdown("### 📥 Download Fixed Resume")
    ats_pdf = create_pdf(rewrite, "ATS-Optimized Resume")
    st.download_button(
        label="Download ATS Resume (PDF)",
        data=ats_pdf,
        file_name="fixed_resume.pdf",
        mime="application/pdf"
    )
else:
    st.info("Upload your resume PDF above.")
