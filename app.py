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
    page_title="My T.A. | AI Teaching Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for TeachAI-inspired Theme
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* My T.A. Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: white;
        padding: 28px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .hero-banner h1 {
        color: #38BDF8 !important;
        margin: 4px 0 6px 0;
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        color: #94A3B8;
        margin: 0;
        font-size: 15px;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
        color: white !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
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
    
    /* Level Cards for Differentiation */
    .level-card {
        background-color: white;
        padding: 16px;
        border-radius: 10px;
        border-left: 5px solid #0284C7;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# 2. Session State Management
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["teacher_name"] = ""
    st.session_state["api_key"] = ""
if "history" not in st.session_state:
    st.session_state["history"] = []

# LOGIN SCREEN
if not st.session_state["authenticated"]:
    st.markdown("""
    <div class="hero-banner">
        <div style="font-size: 54px;">🤖📚</div>
        <h1>My T.A.</h1>
        <p>Your Smart AI Teaching Assistant for NaCCA Lesson Planning & Class Prep</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_login1, col_login2, col_login3 = st.columns([1, 2, 1])
    with col_login2:
        st.subheader("🔐 Teacher Portal Login")
        st.info("Enter your Teacher Name and Gemini API Key to log in.")
        
        teacher_name = st.text_input("👤 Teacher Name", placeholder="e.g., Mr. Mensah")
        api_key_input = st.text_input("🔑 Gemini API Key", type="password", placeholder="Paste your key here...")
        st.markdown("[Get a free Gemini API Key here](https://aistudio.google.com/)")
        
        if st.button("🚀 Enter Studio"):
            if not teacher_name or not api_key_input:
                st.error("Please enter both your name and API key.")
            else:
                st.session_state["authenticated"] = True
                st.session_state["teacher_name"] = teacher_name
                st.session_state["api_key"] = api_key_input
                st.rerun()
    st.stop()

# 3. LOGGED-IN STUDIO APP
with st.sidebar:
    st.markdown(f"### 👋 Welcome, **{st.session_state['teacher_name']}**")
    st.success("My T.A. Active 🟢")
    
    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.session_state["teacher_name"] = ""
        st.session_state["api_key"] = ""
        st.session_state["history"] = []
        st.rerun()
        
    st.divider()
    st.subheader("🗂️ My Session Library")
    if len(st.session_state["history"]) == 0:
        st.caption("No generated items yet in this session.")
    else:
        for idx, item in enumerate(st.session_state["history"]):
            st.markdown(f"**{idx+1}. {item['type']}**")
            st.caption(f"{item['title']} ({item['date']})")

# Top Banner
st.markdown(f"""
<div class="hero-banner">
    <div style="font-size: 42px;">🤖</div>
    <h1>My T.A. Studio</h1>
    <p>Assistant: <strong>{st.session_state['teacher_name']}</strong> | Standard NaCCA Curriculum (Basic 1–9)</p>
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

# MAIN WORKSPACE TABS
tab_plan, tab_diff, tab_tlm = st.tabs([
    "📚 NaCCA Weekly Planner", 
    "🎯 Differentiated Tasks & Quizzes", 
    "🎨 Improvised TLMs & Visuals"
])

# ==========================================
# TAB 1: WEEKLY LESSON PLANNER
# ==========================================
with tab_plan:
    col1, col2 = st.columns(2)
    with col1:
        class_level = st.selectbox("🎯 Class Level", CLASS_LEVELS, key="plan_class")
        subject = st.selectbox("📖 Subject", list(CURRICULUM_DATA.keys()), key="plan_sub")
        strand = st.selectbox("🌿 Strand", list(CURRICULUM_DATA[subject].keys()), key="plan_strand")
    
    with col2:
        sub_strand = st.selectbox("🌱 Sub-Strand", CURRICULUM_DATA[subject][strand], key="plan_substrand")
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

    col_dur1, col_dur2 = st.columns(2)
    with col_dur1:
        duration = st.selectbox("⏱️ Duration per Lesson", ["30 mins", "45 mins", "60 mins", "70 mins", "90 mins", "100 mins (Double Period)"])
    with col_dur2:
        class_size = st.text_input("👥 Class Size", value="40 pupils")
        
    topic = st.text_area("✍️ Lesson Topic & Learning Objectives", placeholder="e.g., Identify equivalent fractions using paper folding activities.", height=100)

    if st.button("🚀 Generate Weekly Lesson Plan Table"):
        if not topic:
            st.warning("⚠️ Please fill in the Lesson Topic & Objectives.")
        elif len(selected_days) == 0:
            st.warning("⚠️ Please select at least one teaching day.")
        else:
            with st.spinner("✨ My T.A. is crafting your NaCCA weekly lesson plan..."):
                try:
                    # Initializing Gemini Client with key
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

                    # Primary generation request using Gemini
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt
                    )
                    
                    raw_html = response.text.replace("```html", "").replace("```", "").strip()
                    
                    st.success(f"🎉 Generated {num_lessons}-Day Lesson Plan for {days_list_str}!")
                    st.components.v1.html(raw_html, height=750, scrolling=True)
                    
                    # Log into session library
                    st.session_state["history"].append({
                        "type": "Lesson Plan",
                        "title": f"{subject} ({class_level})",
                        "date": days_list_str
                    })
                    
                    # Downloads
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
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
                    with col_d2:
                        docx_file = create_docx(topic, f"{subject} - {topic} Lesson Plan")
                        st.download_button(
                            label="📥 Download Word Document (.docx)",
                            data=docx_file,
                            file_name=f"Lesson_Plan_{class_level}_{subject}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                except Exception as e:
                    st.error(f"Error generating lesson plan: {str(e)}")

# ==========================================
# TAB 2: DIFFERENTIATED TASKS & QUIZZES
# ==========================================
with tab_diff:
    st.subheader("🎯 Differentiated Student Tasks & Quiz Generator")
    st.write("Generate tailored activities for different pupil learning speeds plus an end-of-lesson assessment.")
    
    diff_topic = st.text_input("Topic or Concept", placeholder="e.g., Equivalent Fractions or States of Matter")
    diff_class = st.selectbox("Target Class", CLASS_LEVELS, key="diff_class")
    
    if st.button("✨ Generate Differentiated Tasks & Quiz"):
        if not diff_topic:
            st.warning("Please enter a topic.")
        else:
            with st.spinner("My T.A. is building multi-tier exercises and quiz..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    diff_prompt = f"""
                    You are a Ghanaian NaCCA primary/JHS education expert.
                    Create differentiated classroom tasks and an exit ticket quiz for:
                    - Topic: {diff_topic}
                    - Class Level: {diff_class}

                    Format the output cleanly in Markdown:
                    ## 🟢 Tier 1: Basic / Remedial Support Tasks (For pupils needing guidance)
                    (Provide 3 simple guided tasks using concrete objects or step-by-step visuals)

                    ## 🟡 Tier 2: Standard Classwork Tasks (Grade-level standard)
                    (Provide 3 core curriculum exercise questions)

                    ## 🔴 Tier 3: Extension / Fast Learner Tasks (For high achievers)
                    (Provide 2 problem-solving or critical thinking word problems)

                    ---
                    ## 📝 5-Question Exit Ticket / Quiz
                    (5 multiple choice or short answer questions)

                    ## 🔑 Answer Key & Teacher Notes
                    (Solutions for quick grading)
                    """
                    
                    diff_response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=diff_prompt
                    )
                    
                    st.markdown(diff_response.text)
                    
                    st.session_state["history"].append({
                        "type": "Differentiated Tasks",
                        "title": f"{diff_topic} ({diff_class})",
                        "date": "Today"
                    })
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ==========================================
# TAB 3: IMPROVISED LOCAL TLMS & VISUALS
# ==========================================
with tab_tlm:
    st.subheader("🎨 Improvised Local TLMs & Visual Prompt Assistant")
    st.write("Get low-cost Ghanaian classroom material ideas and AI prompts for printable visual aids.")
    
    tlm_topic = st.text_input("Topic for TLM Suggestions", placeholder="e.g., Human Digestive System or Separation of Mixtures")
    
    if st.button("💡 Suggest Improvised Materials & Image Prompts"):
        if not tlm_topic:
            st.warning("Please enter a topic.")
        else:
            with st.spinner("My T.A. is finding local material ideas..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    tlm_prompt = f"""
                    Provide creative teaching resources for Ghanaian schools for the topic: "{tlm_topic}".
                    Include:
                    1. 📦 **Improvised Low-Cost / Zero-Cost TLMs:** (Ideas using everyday items like bottle caps, manila cards, plastic bottles, local seeds, cardboard).
                    2. 🛠️ **How to Construct/Use Them:** Simple steps for the teacher/pupils.
                    3. 🖼️ **AI Visual Prompt for Classroom Chart:** A copyable prompt teachers can use in Canva, Midjourney, or DALL-E to generate a printable chart.
                    """
                    
                    tlm_response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=tlm_prompt
                    )
                    
                    st.markdown(tlm_response.text)
                except Exception as e:
                    st.error(f"Error: {str(
