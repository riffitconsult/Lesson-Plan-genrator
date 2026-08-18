import io
import time
import streamlit as st
from docx import Document
from google import genai

# Try importing WeasyPrint for PDF export
try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except Exception:
    PDF_SUPPORT = False

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="My T.A. | Smart AI Teaching Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 2. ADVANCED CUSTOM CSS STYLING
# ==========================================
st.markdown(
    """
<style>
    /* Global Styling */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Custom Header / Navbar */
    .nav-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 16px 28px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
    }
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .nav-brand h1 {
        color: #38BDF8 !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        letter-spacing: -0.5px;
    }
    .nav-brand span {
        color: #94A3B8;
        font-size: 13px;
        background: rgba(255,255,255,0.08);
        padding: 4px 10px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Stats Banner */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid #E2E8F0;
        transition: transform 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
    }
    .stat-val {
        font-size: 24px;
        font-weight: 800;
        color: #0284C7;
    }
    .stat-lbl {
        font-size: 12px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
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
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0369A1 0%, #075985 100%) !important;
        transform: translateY(-1px);
    }

    /* Badges & Cards */
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

    .testimonial-card {
        background: white;
        padding: 16px;
        border-radius: 12px;
        border-left: 4px solid #38BDF8;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. SESSION STATE & HELPER FUNCTIONS
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["teacher_name"] = ""
    st.session_state["api_key"] = ""
if "history" not in st.session_state:
    st.session_state["history"] = []


def call_gemini_with_retry(client, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
        except Exception as e:
            if (
                "503" in str(e) or "UNAVAILABLE" in str(e)
            ) and attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise e


# ==========================================
# 4. LOGIN SCREEN
# ==========================================
if not st.session_state["authenticated"]:
    st.markdown(
        """
    <div class="nav-container" style="justify-content: center; text-align: center; flex-direction: column; padding: 36px;">
        <div style="font-size: 54px; margin-bottom: 8px;">🤖📚</div>
        <h1 style="color: #38BDF8; font-size: 38px; font-weight: 800; margin: 0;">My T.A.</h1>
        <p style="color: #94A3B8; font-size: 16px; margin-top: 6px;">Your Smart AI Teaching Assistant for Ghanaian NaCCA Curriculum Prep</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.subheader("🔐 Teacher Portal Login")
        st.info(
            "Enter your Teacher Name and Gemini API Key to access your workspace."
        )

        teacher_name = st.text_input(
            "👤 Teacher Name", placeholder="e.g., Mr. Mensah"
        )
        api_key_input = st.text_input(
            "🔑 Gemini API Key", type="password", placeholder="Paste your key here..."
        )
        st.markdown("👉 Get a free Gemini API Key here")

        if st.button("🚀 Enter Studio"):
            if not teacher_name or not api_key_input:
                st.error("Please enter both your name and API key.")
            else:
                st.session_state["authenticated"] = True
                st.session_state["teacher_name"] = teacher_name
                st.session_state["api_key"] = api_key_input
                st.rerun()
    st.stop()

# ==========================================
# 5. LOGGED-IN STUDIO DASHBOARD
# ==========================================

# Sidebar
with st.sidebar:
    st.markdown(f"### 👋 Welcome, {st.session_state['teacher_name']}")
    st.success("My T.A. Active 🟢")

    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.session_state["teacher_name"] = ""
        st.session_state["api_key"] = ""
        st.session_state["history"] = []
        if "generated_html" in st.session_state:
            del st.session_state["generated_html"]
        st.rerun()

    st.divider()
    st.subheader("🗂️ My Session Library")
    if len(st.session_state["history"]) == 0:
        st.caption("No generated items yet in this session.")
    else:
        for idx, item in enumerate(st.session_state["history"]):
            st.markdown(f"{idx+1}. {item['type']}")
            st.caption(f"{item['title']} ({item['date']})")

# Top Header Banner
st.markdown(
    f"""
<div class="nav-container">
    <div class="nav-brand">
        <div style="font-size: 32px;">🤖</div>
        <div>
            <h1>My T.A. Studio</h1>
            <span style="color:#94A3B8; font-size:12px;">Assistant: {st.session_state['teacher_name']} | NaCCA Standard-Based & CCP</span>
        </div>
    </div>
    <div>
        <span style="color:#38BDF8; background:rgba(56, 189, 248, 0.1); padding:6px 12px; border-radius:20px; font-size:13px; border:1px solid rgba(56, 189, 248, 0.3);">
            Basic 1 – Basic 9 (JHS 3)
        </span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Quick Metrics Row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        """<div class="stat-card"><div class="stat-val">9</div><div class="stat-lbl">Core NaCCA Subjects</div></div>""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """<div class="stat-card"><div class="stat-val">B1 – B9</div><div class="stat-lbl">Class Levels Supported</div></div>""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """<div class="stat-card"><div class="stat-val">&lt; 10s</div><div class="stat-lbl">Generation Time</div></div>""",
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        """<div class="stat-card"><div class="stat-val">100% Free</div><div class="stat-lbl">With Gemini Key</div></div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Curriculum Master Data
CURRICULUM_DATA = {
    "Mathematics": {
        "Number": [
            "Whole Numbers, Place Value & Operations",
            "Fractions, Decimals & Percentages",
            "Ratios & Proportions",
        ],
        "Algebra": [
            "Patterns & Relationships",
            "Algebraic Expressions & Equations",
        ],
        "Geometry & Measurement": [
            "Lines, Shapes & 3D Objects",
            "Position & Transformation",
            "Perimeter, Area & Volume",
        ],
        "Data & Probability": [
            "Data Collection & Presentation",
            "Data Analysis & Probability",
        ],
    },
    "Science": {
        "Diversity of Matter": [
            "Living and Non-Living Things",
            "Materials & Mixtures",
            "States of Matter",
        ],
        "Cycles": [
            "Earth Science & Weather",
            "Life Cycles of Organisms",
            "Solar System",
        ],
        "Systems": ["Human Body Systems", "Plant Systems", "Ecosystems"],
        "Forces and Energy": [
            "Sources & Forces of Motion",
            "Electricity & Magnetism",
            "Forms of Energy",
        ],
        "Humans and the Environment": [
            "Personal Hygiene & Sanitation",
            "Diseases & Climate Change",
            "Soil & Agriculture",
        ],
    },
    "English Language": {
        "Oral Language": [
            "Listening & Speaking",
            "Pronunciation & Intonation",
            "Storytelling & Poems",
        ],
        "Reading": [
            "Phonics & Vocabulary",
            "Comprehension Strategies",
            "Silent Reading",
        ],
        "Writing": [
            "Penmanship & Sentence Structure",
            "Composition & Creative Writing",
            "Grammar & Usage",
        ],
        "Literature": ["Folktales, Plays & Poetry Analysis"],
    },
    "French Language": {
        "Oral Expression & Comprehension": [
            "Greetings & Self-Introduction",
            "School & Family Vocabulary",
            "Daily Activities & Directives",
        ],
        "Reading Comprehension": [
            "Simple Texts & Dialogues",
            "Vocabulary Building",
        ],
        "Written Expression": [
            "Short Sentences & Descriptions",
            "Grammar & Conjugation Basics",
        ],
    },
    "Ghanaian Language & Culture": {
        "Oral Language (Listening & Speaking)": [
            "Greeting & Customary Manners",
            "Proverbs, Riddles & Folktales",
            "Customs & Festival Narratives",
        ],
        "Reading & Comprehension": [
            "Local Language Texts & Orthography",
            "Literary Analysis",
        ],
        "Writing & Composition": [
            "Spelling & Grammar Rules",
            "Creative Writing in Ghanaian Language",
        ],
        "Culture & Heritage": [
            "Rites of Passage",
            "Traditional Governance & Values",
        ],
    },
    "Career Technology": {
        "Health and Safety": [
            "Personal & Workshop Safety",
            "Food Hygiene & Environmental Health",
        ],
        "Materials for Production": [
            "Complimentary Materials (Wood, Metal, Plastics)",
            "Food Commodities & Processing",
            "Sewing Materials & Tools",
        ],
        "Tools, Equipment & Processes": [
            "Measuring & Marking Out Tools",
            "Cutting & Shaping Tools",
            "Joining & Finishing Techniques",
        ],
        "Technology & Design": [
            "Designing & Drawing Skills",
            "Modeling & Prototyping",
        ],
        "Entrepreneurship": [
            "Basic Business Management",
            "Marketing & Financial Literacy",
        ],
    },
    "Religious & Moral Education (RME)": {
        "God, His Creation and Attributes": [
            "Attributes of God",
            "Environment & Stewardship",
        ],
        "Religious Practices & Worship": [
            "Islamic, Christian & Traditional Worship Practices",
            "Religious Festivals",
        ],
        "Moral Life & Character": [
            "Honesty, Integrity & Obedience",
            "Manners & Social Values",
        ],
        "Social and Cultural Values": [
            "Family & Community Roles",
            "Conflict Resolution & Peace",
        ],
    },
    "Social Studies": {
        "Environment": [
            "Our Physical & Social Environment",
            "Map Work & Directions",
        ],
        "Family & Community": [
            "Roles in Family & Community",
            "Governance & Citizenship",
        ],
        "Sense of Purpose": ["Culture & National Identity", "Socializing & Values"],
    },
    "Computing": {
        "Introduction to Computing": [
            "Hardware & Peripheral Devices",
            "Operating Systems & Software",
        ],
        "Presentation & Word Processing": [
            "Editing Documents",
            "Formatting Text & Tables",
        ],
        "Internet & Communication": [
            "Web Browsing & E-Safety",
            "Emails & Online Tools",
        ],
        "Programming & Databases": [
            "Basic Coding Concepts",
            "Algorithms & Flowcharts",
        ],
    },
    "Creative Arts": {
        "Visual Arts": ["Drawing, Painting & Design", "Crafts & Sculpture"],
        "Performing Arts": ["Music, Dance & Drama Performances"],
    },
}

CLASS_LEVELS = [
    "Basic 1",
    "Basic 2",
    "Basic 3",
    "Basic 4",
    "Basic 5",
    "Basic 6",
    "Basic 7 (JHS 1)",
    "Basic 8 (JHS 2)",
    "Basic 9 (JHS 3)",
]

# MAIN WORKSPACE TABS
tab_plan, tab_diff, tab_tlm, tab_faq = st.tabs(
    [
        "📚 NaCCA Weekly Planner",
        "🎯 Differentiated Tasks & Quizzes",
        "🎨 Improvised TLMs & Media Generator",
        "❓ FAQ & Teacher Help",
    ]
)

# ==========================================
# TAB 1: WEEKLY LESSON PLANNER
# ==========================================
with tab_plan:
    col1, col2 = st.columns(2)
    with col1:
        class_level = st.selectbox(
            "🎯 Class Level", CLASS_LEVELS, key="plan_class"
        )
        subject = st.selectbox(
            "📖 Subject", list(CURRICULUM_DATA.keys()), key="plan_sub"
        )
        strand = st.selectbox(
            "🌿 Strand", list(CURRICULUM_DATA[subject].keys()), key="plan_strand"
        )

    with col2:
        sub_strand = st.selectbox(
            "🌱 Sub-Strand",
            CURRICULUM_DATA[subject][strand],
            key="plan_substrand",
        )
        code_prefix = (
            "B" + class_level.split(" ")[1] if "Basic" in class_level else "B7"
        )

        content_standard = st.selectbox(
            "🔢 Content Standard Code",
            [
                f"{code_prefix}.1.1",
                f"{code_prefix}.1.2",
                f"{code_prefix}.2.1",
                f"{code_prefix}.2.2",
            ],
        )
        indicator_code = st.selectbox(
            "📍 Indicator Code",
            [
                f"{content_standard}.1",
                f"{content_standard}.2",
                f"{content_standard}.3",
            ],
        )

    st.markdown("---")
    st.subheader("📅 Weekly Teaching Schedule")
    selected_days = st.multiselect(
        "Select the days you teach this lesson:",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        default=["Monday", "Wednesday", "Friday"],
    )

    if selected_days:
        st.markdown(
            "Selected Schedule: "
            + " ".join(
                [f'<span class="day-badge">{day}</span>' for day in selected_days]
            ),
            unsafe_allow_html=True,
        )

    col_dur1, col_dur2 = st.columns(2)
    with col_dur1:
        duration = st.selectbox(
            "⏱️ Duration per Lesson",
            [
                "30 mins",
                "45 mins",
                "60 mins",
                "70 mins",
                "90 mins",
                "100 mins (Double Period)",
            ],
        )
    with col_dur2:
        class_size = st.text_input("👥 Class Size", value="40 pupils")

    topic = st.text_area(
        "✍️ Lesson Topic & Learning Objectives",
        placeholder="e.g., Identify equivalent fractions using paper folding activities.",
        height=100,
    )

    if st.button("🚀 Generate Weekly Lesson Plan Table"):
        if not topic:
            st.warning("⚠️ Please fill in the Lesson Topic & Objectives.")
        elif len(selected_days) == 0:
            st.warning("⚠️ Please select at least one teaching day.")
        else:
            with st.spinner(
                "✨ My T.A. is crafting your NaCCA weekly lesson plan..."
            ):
                try:
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

                    OUTPUT FORMAT RULES:
                    1. Return ONLY pure HTML code inside an <html><body> tag.
                    2. Include CSS styling for clean PDF printing (e.g., table border-collapse: collapse; width: 100%; border: 1px solid #ccc; font-family: sans-serif;).
                    3. Top Header: Display title "WEEKLY LESSON PLAN - {class_level.upper()}".
                    4. Metadata Table: Include Teacher Name, Subject, Class, Strand, Sub-strand, Duration, Content Standard, Indicator Code, Core Competencies, and TLMs.
                    5. Schedule Table: Generate {num_lessons} separate lesson sections for: {days_list_str}.
                    6. Structure each day into the 3 NaCCA phases: STARTER, NEW LEARNING/MAIN, REFLECTION.
                    """

                    response = call_gemini_with_retry(client, prompt)
                    raw_html = (
                        response.text.replace("```html", "")
                        .replace("```", "")
                        .strip()
                    )

                    st.session_state["generated_html"] = raw_html
                    st.session_state["plan_filename"] = f"Lesson_Plan_{subject}_{class_level}".replace(" ", "_")

                    st.session_state["history"].append(
                        {
                            "type": "Lesson Plan",
                            "title": f"{subject} ({class_level})",
                            "date": days_list_str,
                        }
                    )

                except Exception as e:
      
