import streamlit as st
from google import genai
from docx import Document
import io

# Try importing WeasyPrint for PDF export
try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except Exception:
    PDF_SUPPORT = False

# 1. Page Configuration
st.set_page_config(
    page_title="TeachAI Ghana | Lesson Plan Studio",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for TeachAI-inspired Styling
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* TeachAI Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: white;
        padding: 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .hero-banner h1 {
        color: #38BDF8 !important;
        margin: 0 0 8px 0;
        font-size: 32px;
        font-weight: 800;
    }
    .hero-banner p {
        color: #94A3B8;
        margin: 0;
        font-size: 16px;
    }
    
    /* Primary Action Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
        color: white !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25) !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0369A1 0%, #075985 100%) !important;
    }

    /* Day Badges */
    .day-badge {
        background-color: #E0F2FE;
        color: #0369A1;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid #BAE6FD;
        display: inline-block;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# 2. Session State Authentication (Teacher Login)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["teacher_name"] = ""
    st.session_state["api_key"] = ""

# LOGIN SCREEN
if not st.session_state["authenticated"]:
    st.markdown("""
    <div class="hero-banner">
        <h1>🎓 TeachAI Ghana</h1>
        <p>Empower your teaching with AI-generated, NaCCA-aligned weekly lesson plans.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_login1, col_login2, col_login3 = st.columns([1, 2, 1])
    with col_login2:
        st.subheader("🔐 Teacher Login")
        st.info("Log in with your Teacher Name and Gemini API Key to start.")
        
        teacher_name = st.text_input("👤 Teacher Name / Username", placeholder="e.g., Mr. Mensah")
        api_key_input = st.text_input("🔑 Gemini API Key", type="password", placeholder="Paste your API key starting with AIzaSy...")
        st.markdown("[Get a free Gemini API Key here](https://aistudio.google.com/)")
        
        if st.button("🚀 Enter Studio"):
            if not teacher_name or not api_key_input:
                st.error("Please enter both your name and API key to log in.")
            else:
                st.session_state["authenticated"] = True
                st.session_state["teacher_name"] = teacher_name
                st.session_state["api_key"] = api_key_input
                st.rerun()
    st.stop()

# 3. LOGGED-IN STUDIO APP
# Sidebar with Logout
with st.sidebar:
    st.markdown(f"### 👋 Welcome, **{st.session_state['teacher_name']}**")
    st.success("Status: Authenticated 🟢")
    
    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.session_state["teacher_name"] = ""
        st.session_state["api_key"] = ""
        st.rerun()
        
    st.divider()
    st.markdown("### 💡 Quick Guide")
    st.markdown("1. Select Class & Subject.")
    st.markdown("2. Pick specific teaching days.")
    st.markdown("3. Enter your topic and click **Generate**.")

# Hero Header for Logged-in Users
st.markdown(f"""
<div class="hero-banner">
    <h1>🎓 TeachAI Lesson Plan Studio</h1>
    <p>Logged in as: <strong>{st.session_state['teacher_name']}</strong> | Standard NaCCA Curriculum (Basic 1–9)</p>
</div>
""", unsafe_allow_html=True)

# Helper Functions
def create_docx(text, title):
    doc = Document()
    doc.add_heading(title, level=1)
    for line in text.split('\n'):
        if line.startswith('### '):
            doc.add_heading(line.replace('### ', ''), level=3)
        elif line.startswith('## '):
            doc.add_heading(line.replace('## ', ''), level=2)
        elif line.startswith('# '):
            doc.add_heading(line.replace('# ', ''), level=1)
        else:
            doc.add_paragraph(line)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_pdf(html_code):
    buffer = io.BytesIO()
    HTML(string=html_code).write_pdf(target=buffer)
    buffer.seek(0)
    return buffer

# Curriculum Data Dictionary
CURRICULUM_DATA = {
    "Mathematics": {
        "Number": ["Whole Numbers, Place Value & Operations", "Fractions, Decimals & Percentages", "Ratios & Proportions"],
        "Algebra": ["Patterns & Relationships", "Algebraic Expressions & Equations"],
        "Geometry & Measurement": ["Lines, Shapes & 3D Objects", "Position & Transformation", "Perimeter, Area & Volume"],
        "Data & Probability": ["Data Collection & Presentation", "Data Analysis & Probability"]
    },
    "Science": {
        "Diversity of Matter": ["Living and Non-Living Things", "Materials & Mixtures", "States of Matter"],
        "Cycles": ["Earth Science & Weather", "Life Cycles of Organisms", "Solar System"],
        "Systems": ["Human Body Systems", "Plant Systems", "Ecosystems"],
        "Forces and Energy": ["Sources & Forms of Energy", "Forces & Motion", "Electricity & Magnetism"],
        "Humans and the Environment": ["Personal Hygiene & Sanitation", "Diseases & Climate Change", "Soil & Agriculture"]
    },
    "English Language": {
        "Oral Language": ["Listening & Speaking", "Pronunciation & Intonation", "Storytelling & Poems"],
        "Reading": ["Phonics & Vocabulary", "Comprehension Strategies", "Silent Reading"],
        "Writing": ["Penmanship & Sentence Structure", "Composition & Creative Writing", "Grammar & Usage"],
        "Literature": ["Folktales, Plays & Poetry Analysis"]
    },
    "Social Studies": {
        "Environment": ["Our Physical & Social Environment", "Map Work & Directions"],
        "Family & Community": ["Roles in Family & Community", "Governance & Citizenship"],
        "Sense of Purpose": ["Culture & National Identity", "Socializing & Values"]
    },
    "Computing": {
        "Introduction to Computing": ["Hardware & Peripheral Devices", "Operating Systems & Software"],
        "Presentation & Word Processing": ["Editing Documents", "Formatting Text & Tables"],
        "Internet & Communication": ["Web Browsing & E-Safety", "Emails & Online Tools"],
        "Programming & Databases": ["Basic Coding Concepts", "Algorithms & Flowcharts"]
    },
    "Creative Arts": {
        "Visual Arts": ["Drawing, Painting & Design", "Crafts & Sculpture"],
        "Performing Arts": ["Music, Dance & Drama Performances"]
    }
}

CLASS_LEVELS = ["Basic 1", "Basic 2", "Basic 3", "Basic 4", "Basic 5", "Basic 6", "Basic 7 (JHS 1)", "Basic 8 (JHS 2)", "Basic 9 (JHS 3)"]

# Form Layout using Tabs
tab1, tab2 = st.tabs(["📌 Step 1: Curriculum & Schedule", "📝 Step 2: Topic & Objectives"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        class_level = st.selectbox("🎯 Class Level", CLASS_LEVELS)
        subject = st.selectbox("📖 Subject", list(CURRICULUM_DATA.keys()))
        strand = st.selectbox("🌿 Strand", list(CURRICULUM_DATA[subject].keys()))
    
    with col2:
        sub_strand = st.selectbox("🌱 Sub-Strand", CURRICULUM_DATA[subject][strand])
        code_prefix = "B" + class_level.split(" ")[1] if "Basic" in class_level else "B7"
        
        content_standard = st.selectbox("🔢 Content Standard Code", [f"{code_prefix}.1.1", f"{code_prefix}.1.2", f"{code_prefix}.2.1", f"{code_prefix}.2.2"])
        indicator_code = st.selectbox("📍 Indicator Code", [f"{content_standard}.1", f"{content_standard}.2", f"{content_standard}.3"])

    st.markdown("---")
    st.subheader("📅 Weekly Teaching Days")
    selected_days = st.multiselect(
        "Select the days you are teaching this lesson:",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        default=["Monday", "Wednesday", "Friday"]
    )
    
    if selected_days:
        st.markdown("**Selected Schedule:** " + " ".join([f'<span class="day-badge">{day}</span>' for day in selected_days]), unsafe_allow_html=True)

with tab2:
    col_dur1, col_dur2 = st.columns(2)
    with col_dur1:
        duration = st.selectbox("⏱️ Duration per Lesson", ["30 mins", "45 mins", "60 mins", "70 mins", "90 mins", "100 mins (Double Period)"])
    with col_dur2:
        class_size = st.text_input("👥 Class Size", value="40 pupils")
        
    topic = st.text_area("✍️ Lesson Topic & Specific Objectives", placeholder="e.g., Identify equivalent fractions using paper folding activities.", height=120)

st.markdown("---")

# 4. Generate Action
if st.button("🚀 Generate Lesson Plan Table"):
    if not topic:
        st.warning("⚠️ Please fill in the Lesson Topic & Objectives in Step 2.")
    elif len(selected_days) == 0:
        st.warning("⚠️ Please select at least one teaching day in Step 1.")
    else:
        with st.spinner("✨ Crafting your NaCCA-compliant weekly lesson plan..."):
            try:
                # Use stored session API key
                client = genai.Client(api_key=st.session_state["api_key"])
                days_list_str = ", ".join(selected_days)
                num_lessons = len(selected_days)
                
                prompt = f"""
                You are an expert curriculum developer specializing in the Ghanaian NaCCA standard curriculum.
                Generate a complete, professionally formatted weekly lesson plan inside a single self-contained HTML document using styled <table> tags.

                INPUT DETAILS:
                - Teacher Name: {st.session_state['teacher_name']}
                - Class Level: {class_level}
                - Subject: {subject}
                - Strand: {strand}
                - Sub-Strand: {sub_strand}
                - Content Standard Code: {content_standard}
                - Indicator Code: {indicator_code}
                - Duration per Lesson: {duration}
                - Specified Teaching Days: {days_list_str} (Total: {num_lessons} Lessons)
                - Class Size: {class_size}
                - Topic Details & Objectives: {topic}

                SPECIAL INSTRUCTION FOR AI INFERENCE:
                1. AUTOMATICALLY GENERATE appropriate Teaching & Learning Materials (TLMs) suited for a Ghanaian classroom based on the topic.
                2. AUTOMATICALLY GENERATE relevant NaCCA Core Competencies (e.g., Critical Thinking, Collaboration, Communication, Digital Literacy) aligned with the objectives.

                OUTPUT FORMAT RULES:
                1. Return ONLY pure HTML code inside an <html><body> tag. Do NOT wrap it in Markdown code blocks.
                2. Include CSS styling for clean PDF printing (border-collapse, clean blue header banner `#0F172A`, padding, clear borders `#CBD5E1`, A4 page layout).
                3. Top Header: Display ONLY the title "WEEKLY LESSON PLAN - {class_level.upper()}" in the top banner. Do NOT include "Ministry of Education" or "Ghana Education Service".
                4. Metadata Table: Include Teacher Name ({st.session_state['teacher_name']}), Subject, Class, Strand, Sub-strand, Duration, Content Standard, Indicator Code, Core Competencies, and TLMs.
                5. Schedule Table: Generate exactly {num_lessons} separate lesson sections corresponding to: {days_list_str}.
                6. Structure each day's lesson into the 3 mandatory NaCCA phases:
                   - PHASE 1: STARTER (Preparing the brain / revision - 10 mins)
                   - PHASE 2: NEW LEARNING / MAIN (Step-by-step learner activities, group work, inline assessment questions)
                   - PHASE 3: REFLECTION / PLENARY (Learner feedback & summary)
                7. Add a Teacher Evaluation & Remarks box at the bottom.
                """

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                raw_html = response.text.replace("```html", "").replace("```", "").strip()
                
                st.success(f"🎉 Generated {num_lessons}-Day Lesson Plan for {days_list_str}!")
                
                # Render Preview & Downloads
                st.subheader("📋 Lesson Plan Preview")
                st.components.v1.html(raw_html, height=750, scrolling=True)
                
                st.markdown("### 📥 Download Options")
                col_down1, col_down2 = st.columns(2)
                
                with col_down1:
                    if PDF_SUPPORT:
                        pdf_bytes = create_pdf(raw_html)
                        st.download_button(
                            label="📄 Download Printable PDF Table",
                            data=pdf_bytes,
                            file_name=f"Lesson_Plan_{class_level}_{subject}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.warning("PDF engine loading...")

                with col_down2:
                    docx_file = create_docx(topic, f"{subject} - {topic} Lesson Plan")
                    st.download_button(
                        label="📥 Download Word Document (.docx)",
                        data=docx_file,
                        file_name=f"Lesson_Plan_{class_level}_{subject}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

            except Exception as e:
                st.error(f"Error generating lesson plan: {str(e)}")
