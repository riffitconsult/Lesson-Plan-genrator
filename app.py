import streamlit as st
from google import genai
from docx import Document
import io
import time
import datetime

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    PPTX_SUPPORT = True
except Exception:
    PPTX_SUPPORT = False

try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except Exception:
    PDF_SUPPORT = False

st.set_page_config(
    page_title="My T.A. | Smart AI Teaching Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================================
# 1. MOBILE APP STYLING
# ==========================================================
st.markdown("""
<style>
    .stApp {
        background-color: #0F172A;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    /* Constrain everything to a phone-width column and give it a "device" frame */
    .block-container {
        max-width: 430px;
        margin: 0 auto;
        padding-top: 1rem;
        padding-bottom: 6rem;
        background-color: #F8FAFC;
        border-radius: 28px;
        min-height: 100vh;
    }
    #MainMenu, footer, header {visibility: hidden;}

    /* Top status/nav bar */
    .app-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 14px 18px;
        border-radius: 18px;
        margin-bottom: 18px;
        box-shadow: 0 10px 25px -5px rgba(15,23,42,0.25);
    }
    .app-topbar .brand { display:flex; align-items:center; gap:10px; }
    .app-topbar .brand h1 { color:#38BDF8; font-size:20px; font-weight:800; margin:0; letter-spacing:-0.3px; }
    .app-topbar .brand span { color:#94A3B8; font-size:11px; display:block; }
    .app-topbar .badge { color:#38BDF8; background:rgba(56,189,248,0.12); padding:5px 10px; border-radius:16px; font-size:11px; border:1px solid rgba(56,189,248,0.3); }

    /* Section labels */
    .section-label { color:#64748B; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.6px; margin: 14px 4px 8px 4px; }

    /* Primary action cards (Creative Lesson Plan Generator etc) */
    div[data-testid="stButton"] > button.primary-card {
        width:100%;
    }
    .stButton>button {
        width: 100%;
        border-radius: 14px !important;
        font-weight: 600 !important;
        transition: all .15s ease !important;
    }
    .card-btn button {
        background: white !important;
        color:#0F172A !important;
        border:1px solid #E2E8F0 !important;
        padding: 18px 14px !important;
        text-align:left !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }
    .card-btn button:hover { transform: translateY(-2px); border-color:#94A3B8 !important; }

    .hero-btn-plan button { background: linear-gradient(135deg,#0284C7 0%,#0369A1 100%) !important; color:white !important; border:none !important; padding:18px 16px !important; text-align:left !important; box-shadow:0 4px 14px rgba(2,132,199,0.3) !important; }
    .hero-btn-diff button { background: linear-gradient(135deg,#16A34A 0%,#15803D 100%) !important; color:white !important; border:none !important; padding:18px 16px !important; text-align:left !important; box-shadow:0 4px 14px rgba(22,163,74,0.3) !important; }
    .hero-btn-tlm button  { background: linear-gradient(135deg,#1E293B 0%,#0F172A 100%) !important; color:white !important; border:none !important; padding:18px 16px !important; text-align:left !important; box-shadow:0 4px 14px rgba(15,23,42,0.3) !important; }

    /* Grid icon buttons (Improvised TLMs, Supplementary tools) */
    .icon-grid button { background:white !important; color:#0F172A !important; border:1px solid #E2E8F0 !important; border-radius:14px !important; padding:14px 6px !important; font-size:12px !important; }
    .icon-grid button:hover { border-color:#38BDF8 !important; }

    /* Bottom tab bar */
    .bottom-nav-wrap button { border-radius:0 !important; background:transparent !important; color:#64748B !important; font-size:11px !important; box-shadow:none !important; border:none !important; padding:6px 0 !important; }
    .bottom-nav-wrap .nav-active button { color:#0284C7 !important; font-weight:700 !important; }
    .bottom-nav-fixed {
        position: fixed; bottom: 14px; left: 50%; transform: translateX(-50%);
        max-width: 430px; width: calc(100% - 40px);
        background: white; border-radius: 20px; padding: 8px 4px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18); border:1px solid #E2E8F0;
        z-index: 999;
    }

    .stat-card { background:white; border-radius:12px; padding:14px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.04); border:1px solid #E2E8F0; }
    .stat-val { font-size:20px; font-weight:800; color:#0284C7; }
    .stat-lbl { font-size:10px; color:#64748B; text-transform:uppercase; letter-spacing:0.4px; margin-top:2px; }

    .tier-card { background:white; border-radius:12px; padding:12px 14px; border:1px solid #E2E8F0; margin-bottom:8px; }
    .tier-title { font-weight:700; font-size:13px; color:#0F172A; }
    .tier-sub { font-size:11px; color:#64748B; }

    .day-badge { background-color:#E0F2FE; color:#0369A1; padding:4px 10px; border-radius:14px; font-weight:600; font-size:11px; border:1px solid #BAE6FD; display:inline-block; margin-right:5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# 2. SESSION STATE & CURRICULUM DATA
# ==========================================================
DEFAULTS = {
    "authenticated": False,
    "teacher_name": "",
    "api_key": "",
    "history": [],
    "page": "home",
    "lesson_track": None,      # "JHS" or "Primary"
    "feedback_log": [],
    "groups": [],
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def nav_to(page, **kwargs):
    st.session_state["page"] = page
    for k, val in kwargs.items():
        st.session_state[k] = val
    st.rerun()


def call_gemini_with_retry(client, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
        except Exception as e:
            if ("503" in str(e) or "UNAVAILABLE" in str(e)) and attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise e


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
        "Forces and Energy": ["Sources & Forces of Motion", "Electricity & Magnetism", "Forms of Energy"],
        "Humans and the Environment": ["Personal Hygiene & Sanitation", "Diseases & Climate Change", "Soil & Agriculture"]
    },
    "English Language": {
        "Oral Language": ["Listening & Speaking", "Pronunciation & Intonation", "Storytelling & Poems"],
        "Reading": ["Phonics & Vocabulary", "Comprehension Strategies", "Silent Reading"],
        "Writing": ["Penmanship & Sentence Structure", "Composition & Creative Writing", "Grammar & Usage"],
        "Literature": ["Folktales, Plays & Poetry Analysis"]
    },
    "French Language": {
        "Oral Expression & Comprehension": ["Greetings & Self-Introduction", "School & Family Vocabulary", "Daily Activities & Directives"],
        "Reading Comprehension": ["Simple Texts & Dialogues", "Vocabulary Building"],
        "Written Expression": ["Short Sentences & Descriptions", "Grammar & Conjugation Basics"]
    },
    "Ghanaian Language & Culture": {
        "Oral Language (Listening & Speaking)": ["Greeting & Customary Manners", "Proverbs, Riddles & Folktales", "Customs & Festival Narratives"],
        "Reading & Comprehension": ["Local Language Texts & Orthography", "Literary Analysis"],
        "Writing & Composition": ["Spelling & Grammar Rules", "Creative Writing in Ghanaian Language"],
        "Culture & Heritage": ["Rites of Passage", "Traditional Governance & Values"]
    },
    "Career Technology": {
        "Health and Safety": ["Personal & Workshop Safety", "Food Hygiene & Environmental Health"],
        "Materials for Production": ["Complimentary Materials (Wood, Metal, Plastics)", "Food Commodities & Processing", "Sewing Materials & Tools"],
        "Tools, Equipment & Processes": ["Measuring & Marking Out Tools", "Cutting & Shaping Tools", "Joining & Finishing Techniques"],
        "Technology & Design": ["Designing & Drawing Skills", "Modeling & Prototyping"],
        "Entrepreneurship": ["Basic Business Management", "Marketing & Financial Literacy"]
    },
    "Religious & Moral Education (RME)": {
        "God, His Creation and Attributes": ["Attributes of God", "Environment & Stewardship"],
        "Religious Practices & Worship": ["Islamic, Christian & Traditional Worship Practices", "Religious Festivals"],
        "Moral Life & Character": ["Honesty, Integrity & Obedience", "Manners & Social Values"],
        "Social and Cultural Values": ["Family & Community Roles", "Conflict Resolution & Peace"]
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

PRIMARY_LEVELS = ["Basic 1", "Basic 2", "Basic 3", "Basic 4", "Basic 5", "Basic 6"]
JHS_LEVELS = ["Basic 7 (JHS 1)", "Basic 8 (JHS 2)", "Basic 9 (JHS 3)"]
CLASS_LEVELS = PRIMARY_LEVELS + JHS_LEVELS

RESOURCE_LIBRARY = [
    ("NaCCA Curriculum Portal", "Official standards-based curriculum documents for Basic 1-9.", "https://nacca.gov.gh"),
    ("Ghana Education Service (GES)", "Circulars, calendars, and policy guidance for basic schools.", "https://ges.gov.gh"),
    ("EdTech Hub Ghana Resources", "Free low-data teaching resources for Ghanaian classrooms.", "https://edtechhub.org"),
    ("Khan Academy (Aligned Topics)", "Supplementary video explanations for Maths & Science topics.", "https://khanacademy.org"),
]

# ==========================================================
# 3. LOGIN SCREEN
# ==========================================================
if not st.session_state["authenticated"]:
    st.markdown("""
    <div class="app-topbar" style="justify-content:center; text-align:center; flex-direction:column; padding:36px;">
        <div style="font-size:54px; margin-bottom:8px;">🤖📚</div>
        <h1 style="font-size:32px;">My T.A.</h1>
        <span style="font-size:14px; margin-top:6px;">Your Smart AI Teaching Assistant for Ghanaian NaCCA Curriculum Prep</span>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🔑 Teacher Portal Login")
    st.info("Enter your Teacher Name and Gemini API Key to access your workspace.")

    teacher_name = st.text_input("👤 Teacher Name", placeholder="e.g., Mr. Mensah")
    api_key_input = st.text_input("🔐 Gemini API Key", type="password", placeholder="Paste your key here...")
    st.markdown("👉 [Get a free Gemini API Key here](https://aistudio.google.com/apikey)")

    if st.button("🚀 Enter Studio", use_container_width=True):
        if not teacher_name or not api_key_input:
            st.error("Please enter both your name and API key.")
        else:
            st.session_state["authenticated"] = True
            st.session_state["teacher_name"] = teacher_name
            st.session_state["api_key"] = api_key_input
            st.rerun()
    st.stop()

# ==========================================================
# 4. SIDEBAR (Quick Access / Session Library)
# ==========================================================
with st.sidebar:
    st.markdown(f"### 👋 Welcome, {st.session_state['teacher_name']}")
    st.success("My T.A. Active 🟢")

    if st.button("🚪 Logout", use_container_width=True):
        for k in DEFAULTS:
            st.session_state[k] = DEFAULTS[k]
        st.rerun()

    st.divider()
    st.subheader("☰ Quick Access Menu")
    with st.expander("📁 Recent Projects", expanded=False):
        if not st.session_state["history"]:
            st.caption("No generated items yet.")
        for item in st.session_state["history"][-5:][::-1]:
            st.caption(f"**{item['type']}** — {item['title']} ({item['date']})")
    with st.expander("⭐ Favorite Resources", expanded=False):
        for name, desc, url in RESOURCE_LIBRARY[:2]:
            st.caption(f"[{name}]({url})")
    with st.expander("🗓️ Upcoming Events", expanded=False):
        st.caption("No events added yet. Use the Facilitator Network tab to add one.")

    st.divider()
    st.subheader("🗂️ My Session Library")
    if len(st.session_state["history"]) == 0:
        st.caption("No generated items yet in this session.")
    else:
        for idx, item in enumerate(st.session_state["history"]):
            st.markdown(f"**{idx+1}. {item['type']}**")
            st.caption(f"{item['title']} ({item['date']})")

# ==========================================================
# 5. TOP BAR (rendered on every screen except home shows greeting)
# ==========================================================
PAGE_TITLES = {
    "home": ("Facilitators Dashboard", f"Welcome back, {st.session_state['teacher_name']}"),
    "plan": ("Lesson Plan Generator", "Creative NaCCA Weekly Planner"),
    "diff": ("Differentiated Learning Hub", "Tasks & Quizzes, tiered for every learner"),
    "tlm": ("Improvised TLMs & Media", "Zero-cost teaching aids, generated for you"),
    "network": ("Facilitator Network", "Connect with fellow teachers"),
    "library": ("Resource Library", "Curated NaCCA-aligned resources"),
    "analytics": ("Data Analytics", "Your generation activity this session"),
    "feedback": ("Feedback Hub", "Tell us what's working"),
}
title, subtitle = PAGE_TITLES.get(st.session_state["page"], ("My T.A.", ""))

back_col, title_col = st.columns([1, 5])
with back_col:
    if st.session_state["page"] != "home":
        if st.button("←", key="back_btn"):
            nav_to("home")
with title_col:
    st.markdown(f"""
    <div class="app-topbar">
        <div class="brand">
            <div style="font-size:26px;">🤖</div>
            <div>
                <h1>{title}</h1>
                <span>{subtitle}</span>
            </div>
        </div>
        <div class="badge">Basic 1 – Basic 9</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================================
# 6. ROUTER
# ==========================================================
page = st.session_state["page"]

# ---------- HOME ----------
if page == "home":
    c1, c2, c3, c4 = st.columns(4)
    stats = [("9", "NaCCA Subjects"), ("B1–B9", "Class Levels"), (str(len(st.session_state["history"])), "Items Generated"), ("100% Free", "With Gemini Key")]
    for col, (val, lbl) in zip([c1, c2, c3, c4], stats):
        with col:
            st.markdown(f'<div class="stat-card"><div class="stat-val" style="font-size:15px;">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Main Tools</div>', unsafe_allow_html=True)

    st.markdown('<div class="hero-btn-plan">', unsafe_allow_html=True)
    if st.button("📅  CREATIVE LESSON PLAN GENERATOR", use_container_width=True, key="hero_plan"):
        nav_to("plan")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="hero-btn-diff">', unsafe_allow_html=True)
    if st.button("🎯  INCLUSIVE DIFFERENTIATED TASKS & QUIZZES", use_container_width=True, key="hero_diff"):
        nav_to("diff")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="hero-btn-tlm">', unsafe_allow_html=True)
    if st.button("🎨  IMPROVISED TLMs & DYNAMIC VISUALS", use_container_width=True, key="hero_tlm"):
        nav_to("tlm")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Improvised TLMs — Quick Access</div>', unsafe_allow_html=True)
    st.markdown('<div class="icon-grid">', unsafe_allow_html=True)
    tlm_cols = st.columns(3)
    tlm_shortcuts = [
        ("📊 PPT Generator", "ppt"), ("📚 TLM Library", "library_tool"), ("🎨 Visual Assets", "visual"),
        ("🖥️ Whiteboard", "whiteboard"), ("🏺 Model Kits", "models"), ("🎙️ Podcast Script", "podcast"),
    ]
    for i, (label, tool_key) in enumerate(tlm_shortcuts):
        with tlm_cols[i % 3]:
            if st.button(label, key=f"shortcut_{tool_key}", use_container_width=True):
                nav_to("tlm", tlm_open=tool_key)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Supplementary Tools & Resources</div>', unsafe_allow_html=True)
    st.markdown('<div class="icon-grid">', unsafe_allow_html=True)
    supp_cols = st.columns(4)
    supp_items = [("🤝 Facilitator\nNetwork", "network"), ("📖 Resource\nLibrary", "library"), ("📈 Data\nAnalytics", "analytics"), ("💬 Feedback\nHub", "feedback")]
    for col, (label, dest) in zip(supp_cols, supp_items):
        with col:
            if st.button(label, key=f"supp_{dest}", use_container_width=True):
                nav_to(dest)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- PLAN (Creative Lesson Plan Generator) ----------
elif page == "plan":
    if st.session_state["lesson_track"] is None:
        st.markdown('<div class="section-label">Choose a Track</div>', unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown('<div class="card-btn">', unsafe_allow_html=True)
            if st.button("🎓\n\nJHS Lesson Plans", use_container_width=True):
                st.session_state["lesson_track"] = "JHS"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with cc2:
            st.markdown('<div class="card-btn">', unsafe_allow_html=True)
            if st.button("🧩\n\nPrimary Lesson Plans", use_container_width=True):
                st.session_state["lesson_track"] = "Primary"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        track = st.session_state["lesson_track"]
        levels_for_track = JHS_LEVELS if track == "JHS" else PRIMARY_LEVELS
        if st.button(f"↺ Switch track (currently {track})"):
            st.session_state["lesson_track"] = None
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            class_level = st.selectbox("🎯 Class Level", levels_for_track, key="plan_class")
            subject = st.selectbox("📘 Subject", list(CURRICULUM_DATA.keys()), key="plan_sub")
            strand = st.selectbox("🌿 Strand", list(CURRICULUM_DATA[subject].keys()), key="plan_strand")
        with col2:
            sub_strand = st.selectbox("🌱 Sub-Strand", CURRICULUM_DATA[subject][strand], key="plan_substrand")
            code_prefix = "B" + class_level.split(" ")[1] if "Basic" in class_level else "B7"
            content_standard = st.selectbox("🔢 Content Standard Code",
                [f"{code_prefix}.1.1", f"{code_prefix}.1.2", f"{code_prefix}.2.1", f"{code_prefix}.2.2"])
            indicator_code = st.selectbox("📍 Indicator Code",
                [f"{content_standard}.1", f"{content_standard}.2", f"{content_standard}.3"])

        st.markdown("---")
        st.subheader("🗓️ Weekly Teaching Schedule")
        selected_days = st.multiselect("Select the days you teach this lesson:",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            default=["Monday", "Wednesday", "Friday"])

        if selected_days:
            st.markdown("**Selected Schedule:** " + " ".join([f'<span class="day-badge">{d}</span>' for d in selected_days]), unsafe_allow_html=True)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            duration = st.selectbox("⏱️ Duration per Lesson", ["30 mins", "45 mins", "60 mins", "70 mins", "90 mins", "100 mins (Double Period)"])
        with col_d2:
            class_size = st.text_input("👥 Class Size", value="40 pupils")

        topic = st.text_area("✍️ Lesson Topic & Learning Objectives",
            placeholder="e.g., Identify equivalent fractions using paper folding activities.", height=100)

        if st.button("🚀 Generate Weekly Lesson Plan Table", use_container_width=True):
            if not topic:
                st.warning("⚠️ Please fill in the Lesson Topic & Objectives.")
            elif len(selected_days) == 0:
                st.warning("⚠️ Please select at least one teaching day.")
            else:
                with st.spinner("✨ My T.A. is crafting your NaCCA weekly lesson plan..."):
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
                        2. Include CSS styling for clean PDF printing.
                        3. Top Header: Display title "WEEKLY LESSON PLAN - {class_level.upper()}".
                        4. Metadata Table: Include Teacher Name, Subject, Class, Strand, Sub-strand, Duration, Content Standard, Indicator Code, Core Competencies, and TLMs.
                        5. Schedule Table: Generate {num_lessons} separate lesson sections for: {days_list_str}.
                        6. Structure each day into the 3 NaCCA phases: STARTER, NEW LEARNING/MAIN, REFLECTION.
                        """
                        response = call_gemini_with_retry(client, prompt)
                        raw_html = response.text.replace("```html", "").replace("```", "").strip()

                        st.success(f"🎉 Generated {num_lessons}-Day Lesson Plan for {days_list_str}!")
                        st.components.v1.html(raw_html, height=750, scrolling=True)

                        st.session_state["history"].append({
                            "type": "Lesson Plan",
                            "title": f"{subject} ({class_level})",
                            "date": days_list_str
                        })
                    except Exception as e:
                        st.error(f"Error generating lesson plan: {str(e)}")

# ---------- DIFFERENTIATED LEARNING HUB ----------
elif page == "diff":
    st.markdown('<div class="section-label">Differentiated Tasks</div>', unsafe_allow_html=True)
    tier_cols = st.columns(3)
    tiers = [
        ("Tier 1: Foundation", "Visual & Basic Q"),
        ("Tier 2: Intermediate", "Applied Problems"),
        ("Tier 3: Advanced", "Project-Based & Open-Ended"),
    ]
    for col, (t_title, t_sub) in zip(tier_cols, tiers):
        with col:
            st.markdown(f'<div class="tier-card"><div class="tier-title">{t_title}</div><div class="tier-sub">{t_sub}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Customized Quizzes</div>', unsafe_allow_html=True)
    quiz_cols = st.columns(3)
    quiz_types = [
        ("Differentiated", "Variable Complexity Qs"),
        ("Adaptive", "Levels adjust per student"),
        ("Question Bank", "Search & Build"),
    ]
    for col, (q_title, q_sub) in zip(quiz_cols, quiz_types):
        with col:
            st.markdown(f'<div class="tier-card"><div class="tier-title">{q_title}</div><div class="tier-sub">{q_sub}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    diff_topic = st.text_input("Topic or Concept", placeholder="e.g., Equivalent Fractions or States of Matter")
    diff_class = st.selectbox("Target Class", CLASS_LEVELS, key="diff_class")
    quiz_style = st.selectbox("Quiz Style", ["Differentiated (mixed complexity)", "Adaptive (levels per student)", "Build from Question Bank"])

    gcol1, gcol2 = st.columns(2)
    with gcol1:
        generate_clicked = st.button("✨ Create Assignment / Quiz", use_container_width=True)
    with gcol2:
        manage_clicked = st.button("👥 Manage Groups", use_container_width=True)

    if manage_clicked:
        st.session_state["show_groups"] = not st.session_state.get("show_groups", False)

    if st.session_state.get("show_groups", False):
        st.markdown('<div class="section-label">Manage Groups</div>', unsafe_allow_html=True)
        new_group = st.text_input("Add a new group name", placeholder="e.g., Group A - Remedial")
        if st.button("➕ Add Group"):
            if new_group:
                st.session_state["groups"].append(new_group)
        if st.session_state["groups"]:
            for g in st.session_state["groups"]:
                st.markdown(f"- {g}")
        else:
            st.caption("No groups added yet.")

    if generate_clicked:
        if not diff_topic:
            st.warning("Please enter a topic.")
        else:
            with st.spinner("My T.A. is building multi-tier exercises and quiz..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    diff_prompt = f"""
                    Create differentiated classroom tasks (Tier 1 Foundation - visual/basic, Tier 2 Intermediate - applied problems,
                    Tier 3 Advanced - project-based/open-ended) and a {quiz_style} exit ticket quiz for:
                    - Topic: {diff_topic}
                    - Class Level: {diff_class}
                    Format clearly with headers for each tier and the quiz.
                    """
                    diff_response = call_gemini_with_retry(client, diff_prompt)
                    st.markdown(diff_response.text)
                    st.session_state["history"].append({"type": "Differentiated Tasks & Quiz", "title": f"{diff_topic} ({diff_class})", "date": datetime.date.today().isoformat()})
                except Exception as e:
                    st.error(f"Error generating tasks: {str(e)}")

# ---------- IMPROVISED TLMs & MEDIA ----------
elif page == "tlm":
    open_tool = st.session_state.pop("tlm_open", None) if "tlm_open" in st.session_state else st.session_state.get("tlm_open")
    tool_labels = {
        "ppt": "📊 PPT Presentation Generator",
        "library_tool": "📚 TLM Library",
        "visual": "🎨 Visual Asset Generator",
        "whiteboard": "🖥️ Interactive Whiteboard Tools",
        "models": "🏺 Physical Model Kits",
        "podcast": "🎙️ Audio / Podcast Script Creator",
    }
    default_index = list(tool_labels.keys()).index(open_tool) if open_tool in tool_labels else 0
    tool = st.radio("Choose a tool", list(tool_labels.values()), index=default_index, horizontal=False)
    st.markdown("---")

    tlm_topic = st.text_input("Topic", placeholder="e.g., Human Digestive System or Separation of Mixtures", key="tlm_topic")
    tlm_class = st.selectbox("Class Level", CLASS_LEVELS, key="tlm_class")

    # ---- PPT Presentation Generator ----
    if tool == tool_labels["ppt"]:
        num_slides = st.slider("Number of slides", 3, 12, 6)
        if st.button("💡 Generate PowerPoint", use_container_width=True):
            if not tlm_topic:
                st.warning("Please enter a topic.")
            elif not PPTX_SUPPORT:
                st.error("python-pptx is not installed in this environment.")
            else:
                with st.spinner("My T.A. is drafting your slide deck..."):
                    try:
                        client = genai.Client(api_key=st.session_state["api_key"])
                        ppt_prompt = f"""
                        Create an outline for a {num_slides}-slide classroom presentation on "{tlm_topic}" for {tlm_class} pupils
                        in Ghana, aligned to the NaCCA curriculum.
                        Return ONLY plain text, one slide per block, in this exact format with no extra commentary:
                        SLIDE: <slide title>
                        - <bullet 1>
                        - <bullet 2>
                        - <bullet 3>
                        (repeat for each slide)
                        """
                        response = call_gemini_with_retry(client, ppt_prompt)
                        raw = response.text.strip()

                        slides_data = []
                        current_title, current_bullets = None, []
                        for line in raw.splitlines():
                            line = line.strip()
                            if line.upper().startswith("SLIDE:"):
                                if current_title:
                                    slides_data.append((current_title, current_bullets))
                                current_title = line.split(":", 1)[1].strip()
                                current_bullets = []
                            elif line.startswith("-"):
                                current_bullets.append(line.lstrip("- ").strip())
                        if current_title:
                            slides_data.append((current_title, current_bullets))

                        prs = Presentation()
                        title_slide_layout = prs.slide_layouts[0]
                        bullet_layout = prs.slide_layouts[1]

                        slide = prs.slides.add_slide(title_slide_layout)
                        slide.shapes.title.text = tlm_topic
                        slide.placeholders[1].text = f"{tlm_class} | My T.A. Studio"

                        for s_title, bullets in slides_data:
                            slide = prs.slides.add_slide(bullet_layout)
                            slide.shapes.title.text = s_title
                            body = slide.placeholders[1].text_frame
                            body.clear()
                            for i, b in enumerate(bullets):
                                p = body.paragraphs[0] if i == 0 else body.add_paragraph()
                                p.text = b

                        buf = io.BytesIO()
                        prs.save(buf)
                        buf.seek(0)

                        st.success(f"🎉 Generated a {len(slides_data)+1}-slide deck on {tlm_topic}!")
                        st.download_button("⬇️ Download .pptx", data=buf, file_name=f"{tlm_topic.replace(' ', '_')}.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
                        st.session_state["history"].append({"type": "PPT Deck", "title": tlm_topic, "date": tlm_class})
                    except Exception as e:
                        st.error(f"Error generating PPT: {str(e)}")

    # ---- TLM Library ----
    elif tool == tool_labels["library_tool"]:
        st.caption("Search for zero-cost, locally-sourced teaching aid ideas.")
        if st.button("🔎 Find TLM Ideas", use_container_width=True):
            if not tlm_topic:
                st.warning("Please enter a topic.")
            else:
                with st.spinner("Searching the improvised-materials library..."):
                    try:
                        client = genai.Client(api_key=st.session_state["api_key"])
                        lib_prompt = f"""
                        List 6 zero-cost or low-cost improvised Teaching & Learning Materials (TLMs) a Ghanaian
                        basic school teacher could make locally to teach "{tlm_topic}" to {tlm_class} pupils.
                        For each, give: Material name, what it's made from (locally available items in Ghana), and how to use it in class.
                        """
                        response = call_gemini_with_retry(client, lib_prompt)
                        st.markdown(response.text)
                        st.session_state["history"].append({"type": "TLM Library", "title": tlm_topic, "date": tlm_class})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # ---- Visual Asset Generator ----
    elif tool == tool_labels["visual"]:
        st.caption("Generates a hand-drawable diagram/chart spec — no image API required, just chalk & marker instructions.")
        if st.button("🖼️ Generate Visual Asset Spec", use_container_width=True):
            if not tlm_topic:
                st.warning("Please enter a topic.")
            else:
                with st.spinner("Designing a chalkboard-friendly visual..."):
                    try:
                        client = genai.Client(api_key=st.session_state["api_key"])
                        visual_prompt = f"""
                        Design a simple, clearly labeled chalkboard/poster diagram a Ghanaian teacher can hand-draw
                        to explain "{tlm_topic}" to {tlm_class} pupils. Describe: layout, labels, colors to use with
                        chalk or markers, and a step-by-step drawing sequence.
                        """
                        response = call_gemini_with_retry(client, visual_prompt)
                        st.markdown(response.text)
                        st.session_state["history"].append({"type": "Visual Asset", "title": tlm_topic, "date": tlm_class})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # ---- Interactive Whiteboard Tools ----
    elif tool == tool_labels["whiteboard"]:
        st.info("🚧 Live interactive whiteboard is coming soon. In the meantime, generate a guided whiteboard activity script:")
        if st.button("🖊️ Generate Whiteboard Activity", use_container_width=True):
            if not tlm_topic:
                st.warning("Please enter a topic.")
            else:
                with st.spinner("Scripting a whiteboard walkthrough..."):
                    try:
                        client = genai.Client(api_key=st.session_state["api_key"])
                        wb_prompt = f"""
                        Write a step-by-step interactive whiteboard activity (5-8 steps) a teacher can lead, live,
                        to teach "{tlm_topic}" to {tlm_class} pupils, including what to write/draw at each step and
                        a question to ask pupils at each step.
                        """
                        response = call_gemini_with_retry(client, wb_prompt)
                        st.markdown(response.text)
                        st.session_state["history"].append({"type": "Whiteboard Activity", "title": tlm_topic, "date": tlm_class})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # ---- Physical Model Kits ----
    elif tool == tool_labels["models"]:
        if st.button("🏺 Generate Model Kit Instructions", use_container_width=True):
            if not tlm_topic:
                st.warning("Please enter a topic.")
            else:
                with st.spinner("Designing a physical model build..."):
                    try:
                        client = genai.Client(api_key=st.session_state["api_key"])
                        model_prompt = f"""
                        Design a physical model or hands-on kit a Ghanaian teacher and pupils can build with cheap
                        local materials to demonstrate "{tlm_topic}" to {tlm_class} pupils.
                        Provide: materials list (with rough GH₵ cost if any), build steps, and how to use it in the lesson.
                        """
                        response = call_gemini_with_retry(client, model_prompt)
                        st.markdown(response.text)
                        st.session_state["history"].append({"type": "Physical Model Kit", "title": tlm_topic, "date": tlm_class})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # ---- Audio / Podcast Script Creator ----
    elif tool == tool_labels["podcast"]:
        duration_choice = st.selectbox("Target length", ["1-2 minutes", "3-5 minutes", "5-8 minutes"])
        if st.button("🎙️ Generate Script", use_container_width=True):
            if not tlm_topic:
                st.warning("Please enter a topic.")
            else:
                with st.spinner("Writing an audio script..."):
                    try:
                        client = genai.Client(api_key=st.session_state["api_key"])
                        podcast_prompt = f"""
                        Write a {duration_choice} audio/podcast-style script explaining "{tlm_topic}" to {tlm_class}
                        pupils in Ghana. Use a warm, conversational teacher voice, simple language, and a short
                        recap question at the end.
                        """
                        response = call_gemini_with_retry(client, podcast_prompt)
                        st.markdown(response.text)
                        st.session_state["history"].append({"type": "Podcast Script", "title": tlm_topic, "date": tlm_class})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ---------- FACILITATOR NETWORK ----------
elif page == "network":
    st.caption("Connect with fellow facilitators teaching the same subject/class level. (Local, session-based directory — no data leaves this session.)")
    with st.form("network_form"):
        n_name = st.text_input("Your display name for the network", value=st.session_state["teacher_name"])
        n_subject = st.selectbox("Subject you teach", list(CURRICULUM_DATA.keys()))
        n_note = st.text_area("A note or question for other facilitators", placeholder="e.g., Looking for Basic 6 Maths pacing tips")
        submitted = st.form_submit_button("📌 Post to Network")
    if submitted and n_note:
        st.session_state.setdefault("network_posts", []).insert(0, {"name": n_name, "subject": n_subject, "note": n_note})
        st.success("Posted for this session.")
    st.markdown('<div class="section-label">Recent Posts</div>', unsafe_allow_html=True)
    posts = st.session_state.get("network_posts", [])
    if not posts:
        st.caption("No posts yet this session — be the first to share.")
    for p in posts:
        st.markdown(f'<div class="tier-card"><div class="tier-title">{p["name"]} · {p["subject"]}</div><div class="tier-sub">{p["note"]}</div></div>', unsafe_allow_html=True)

# ---------- RESOURCE LIBRARY ----------
elif page == "library":
    search = st.text_input("🔎 Search resources", placeholder="e.g., NaCCA, Maths, low-data")
    for name, desc, url in RESOURCE_LIBRARY:
        if search.lower() in name.lower() or search.lower() in desc.lower() or not search:
            st.markdown(f'<div class="tier-card"><div class="tier-title"><a href="{url}" target="_blank">{name}</a></div><div class="tier-sub">{desc}</div></div>', unsafe_allow_html=True)

# ---------- DATA ANALYTICS ----------
elif page == "analytics":
    history = st.session_state["history"]
    if not history:
        st.info("No activity yet this session. Generate a lesson plan, quiz, or TLM to see stats here.")
    else:
        type_counts = {}
        for item in history:
            type_counts[item["type"]] = type_counts.get(item["type"], 0) + 1
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="stat-card"><div class="stat-val">{len(history)}</div><div class="stat-lbl">Total Items Generated</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card"><div class="stat-val">{len(type_counts)}</div><div class="stat-lbl">Tool Types Used</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Breakdown by Type</div>', unsafe_allow_html=True)
        st.bar_chart(type_counts)
        st.markdown('<div class="section-label">Full Session Log</div>', unsafe_allow_html=True)
        for item in history[::-1]:
            st.markdown(f"- **{item['type']}** — {item['title']} ({item['date']})")

# ---------- FEEDBACK HUB ----------
elif page == "feedback":
    rating = st.slider("How is My T.A. working for you today?", 1, 5, 4)
    fb_text = st.text_area("Tell us more (optional)", placeholder="What worked well? What would you change?")
    if st.button("📨 Submit Feedback", use_container_width=True):
        st.session_state["feedback_log"].append({"rating": rating, "text": fb_text, "date": datetime.date.today().isoformat()})
        st.success("Thanks — your feedback was recorded for this session.")
    if st.session_state["feedback_log"]:
        st.markdown('<div class="section-label">Your Feedback This Session</div>', unsafe_allow_html=True)
        for f in st.session_state["feedback_log"][::-1]:
            st.markdown(f"- {'⭐'*f['rating']} — {f['text'] or '(no comment)'}")

# ==========================================================
# 7. BOTTOM TAB BAR
# ==========================================================
st.markdown('<div class="bottom-nav-fixed"><div class="bottom-nav-wrap">', unsafe_allow_html=True)
nav_items = [("home", "🏠", "Home"), ("plan", "📘", "Plan"), ("diff", "🎯", "Tasks"), ("tlm", "🎨", "TLM"), ("analytics", "📈", "Stats")]
nav_cols = st.columns(len(nav_items))
for col, (key, icon, label) in zip(nav_cols, nav_items):
    with col:
        active_class = "nav-active" if st.session_state["page"] == key else ""
        st.markdown(f'<div class="{active_class}">', unsafe_allow_html=True)
        if st.button(f"{icon}\n{label}", key=f"bottomnav_{key}", use_container_width=True):
            nav_to(key)
        st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)
