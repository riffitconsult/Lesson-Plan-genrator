import streamlit as st
from google import genai
import time

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="PlanAhead: AI Lesson Wizard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. RESPONSIVE CSS STYLING
# ==========================================
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top Navigation Bar */
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #FFFFFF;
        padding: 12px 24px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .brand-title {
        font-size: 20px;
        font-weight: 700;
        color: #0F172A;
    }
    .user-profile {
        font-size: 14px;
        color: #475569;
        font-weight: 500;
    }

    /* Sidebar Navigation Padding */
    div[data-testid="stSidebarNav"] {
        padding-top: 10px;
    }
    
    /* Card Styling */
    .dashboard-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        background-color: #0284C7 !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

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
                model='gemini-2.5-flash',
                contents=prompt
            )
        except Exception as e:
            if ("503" in str(e) or "UNAVAILABLE" in str(e)) and attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise e

# ==========================================
# 4. MASTER CURRICULUM DATA
# ==========================================
CURRICULUM_DATA = {
    "Mathematics": {
        "Number": ["Whole Numbers, Place Value & Operations", "Fractions, Decimals & Percentages"],
        "Algebra": ["Patterns & Relationships", "Algebraic Expressions & Equations"],
        "Geometry & Measurement": ["Lines, Shapes & 3D Objects", "Perimeter, Area & Volume"],
        "Data & Probability": ["Data Collection & Presentation", "Data Analysis & Probability"]
    },
    "Science": {
        "Diversity of Matter": ["Living and Non-Living Things", "Materials & Mixtures", "States of Matter"],
        "Cycles": ["Earth Science & Weather", "Life Cycles of Organisms"],
        "Systems": ["Human Body Systems", "Plant Systems", "Ecosystems"],
        "Forces and Energy": ["Sources & Forces of Motion", "Electricity & Magnetism"]
    },
    "French Language": {
        "Oral Expression & Comprehension": ["Greetings & Self-Introduction", "School & Family Vocabulary", "Daily Directives"],
        "Reading Comprehension": ["Simple Texts & Dialogues", "Vocabulary Building"],
        "Written Expression": ["Short Sentences & Descriptions", "Grammar & Conjugation"]
    },
    "English Language": {
        "Oral Language": ["Listening & Speaking", "Pronunciation & Intonation", "Storytelling & Poems"],
        "Reading": ["Phonics & Vocabulary", "Comprehension Strategies", "Silent Reading"],
        "Writing": ["Penmanship & Sentence Structure", "Composition & Creative Writing", "Grammar & Usage"],
        "Literature": ["Folktales, Plays & Poetry Analysis"]
    },
    "Ghanaian Language & Culture": {
        "Oral Language": ["Greeting & Customary Manners", "Proverbs & Folktales"],
        "Reading & Comprehension": ["Local Language Texts & Orthography"],
        "Culture & Heritage": ["Rites of Passage", "Traditional Governance & Values"]
    },
    "Career Technology": {
        "Health and Safety": ["Personal & Workshop Safety", "Food Hygiene"],
        "Materials for Production": ["Wood, Metal, Plastics", "Food Commodities & Processing"],
        "Tools & Processes": ["Measuring & Marking Out Tools", "Cutting & Shaping Tools"]
    },
    "Religious & Moral Education (RME)": {
        "God, Creation & Attributes": ["Attributes of God", "Environment & Stewardship"],
        "Religious Practices": ["Worship Practices", "Religious Festivals"],
        "Moral Life": ["Honesty, Integrity & Manners"]
    },
    "Social Studies": {
        "Environment": ["Physical & Social Environment", "Map Work"],
        "Family & Community": ["Roles in Family & Community", "Governance & Citizenship"]
    },
    "Computing": {
        "Introduction to Computing": ["Hardware & Peripheral Devices", "Operating Systems"],
        "Applications": ["Word Processing & Spreadsheets", "Web Browsing & E-Safety"]
    }
}

CLASS_LEVELS = ["Basic 1", "Basic 2", "Basic 3", "Basic 4", "Basic 5", "Basic 6", "Basic 7 (JHS 1)", "Basic 8 (JHS 2)", "Basic 9 (JHS 3)"]

# ==========================================
# 5. LOGIN SCREEN
# ==========================================
if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center;'>🔐 PlanAhead Teacher Portal Login</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        teacher_name = st.text_input("👤 Teacher Name", placeholder="e.g., Mme. Dupont / Mr. Mensah")
        api_key_input = st.text_input("🔑 Gemini API Key", type="password", placeholder="Paste API key here...")
        if st.button("🚀 Enter Portal"):
            if teacher_name and api_key_input:
                st.session_state["authenticated"] = True
                st.session_state["teacher_name"] = teacher_name
                st.session_state["api_key"] = api_key_input
                st.rerun()
            else:
                st.error("Please provide both your name and API key.")
    st.stop()

# ==========================================
# 6. NAVIGATION SIDEBAR (IMAGE 3 ITEMS)
# ==========================================
with st.sidebar:
    st.markdown("### 📘 **PlanAhead**")
    st.caption(f"Logged in: {st.session_state['teacher_name']}")
    st.divider()

    # Image 3 Navigation Options
    nav_choice = st.radio(
        "NAVIGATION",
        [
            "📝 Lesson Plan Generator",
            "🎯 Differentiated Tasks & Quizzes",
            "🎨 Improvised TLMs & Visuals",
            "❓ FAQ"
        ]
    )

    st.divider()
    
    # Image 3 Recent Plans Section
    st.markdown("### 🕒 **Recent Plans**")
    if len(st.session_state["history"]) == 0:
        st.caption("• French (Basic 8) - Salutations")
        st.caption("• Basic 7 Science - Ecosystems")
    else:
        for item in st.session_state["history"][-5:]:
            st.caption(f"• {item['title']}")

    st.divider()
    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

# ==========================================
# 7. TOP HEADER NAVBAR
# ==========================================
st.markdown(f"""
<div class="top-navbar">
    <div class="brand-title">📘 PlanAhead: AI Lesson Wizard</div>
    <div class="user-profile">👤 {st.session_state['teacher_name']}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 8. ROUTING BASED ON SIDEBAR SELECTION
# ==========================================

# --- PAGE 1: LESSON PLAN GENERATOR ---
if nav_choice == "📝 Lesson Plan Generator":
    
    col_left, col_middle, col_right = st.columns([1.2, 1.5, 1])

    # Left Column: Inputs, Language & Community Context
    with col_left:
        st.markdown("### Step 1: Lesson Details")
        
        # Output Language Selector
        plan_language = st.selectbox(
            "🌐 Output Language", 
            ["English 🇬🇧", "Français 🇫🇷 (French)", "English with French Terminology"]
        )
        
        subject = st.selectbox("Subject", list(CURRICULUM_DATA.keys()))
        strand = st.selectbox("Strand", list(CURRICULUM_DATA[subject].keys()))
        topic_input = st.text_input("Topic", value="Se présenter et saluer / Greetings")
        
        grade_level = st.selectbox("Grade Level", CLASS_LEVELS)
        duration = st.selectbox("Duration", ["30 min", "45 min", "60 min", "90 min"])

        st.markdown("---")
        st.markdown("### 🏡 Context & Environment")
        community_context = st.text_area(
            "Classroom & Community Context",
            placeholder="e.g., Rural farming community, large class size (50+ students), mixed-ability learners, limited internet access.",
            height=90
        )
        
        if st.button("🚀 Generate Draft"):
            if topic_input:
                with st.spinner("Generating customized lesson plan..."):
                    try:
                        client = genai.Client(api_key=st.session_state["api_key"])
                        
                        lang_instruction = "Write the ENTIRE lesson plan strictly in FRENCH language." if "Français" in plan_language else "Write the lesson plan in English."
                        
                        prompt = f"""
                        You are an expert curriculum planner. Generate a comprehensive weekly lesson plan.
                        
                        SETTINGS & CONTEXT:
                        - Target Output Language: {plan_language} ({lang_instruction})
                        - Subject: {subject}
                        - Strand: {strand}
                        - Topic: {topic_input}
                        - Class Level: {grade_level}
                        - Duration: {duration}
                        - Classroom Environment & Community Context: {community_context if community_context else 'Standard classroom setup'}
                        
                        INSTRUCTIONS:
                        1. Structure into 3 clear phases: Starter (Warm-up), Main Learning Activities, and Reflection/Assessment.
                        2. Actively adapt activities and teaching aids to match the provided Community Context and Classroom Environment.
                        """
                        
                        res = call_gemini_with_retry(client, prompt)
                        st.session_state["current_plan"] = res.text
                        st.session_state["history"].append({"title": f"{subject}: {topic_input} ({plan_language})"})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Middle Column: Preview & Edit Area
    with col_middle:
        st.markdown("### Lesson Preview & Edit")
        plan_content = st.session_state.get("current_plan", "Select details on the left and click 'Generate Draft' to create your lesson plan preview here.")
        edited_plan = st.text_area("Drafting Area", value=plan_content, height=520)
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            st.button("💾 Save Plan")
        with c_btn2:
            st.button("📤 Export Plan")

    # Right Column: AI Suggestions
    with col_right:
        st.markdown("### AI Suggestions")
        st.markdown("""
        <div class="dashboard-card">
            <strong>💡 Environmental Adaptation</strong><br>
            <small>Incorporating rural or urban community references increases student engagement by up to 40%.</small>
        </div>
        <div class="dashboard-card">
            <strong>🗣️ French Immersion Tip</strong><br>
            <small>Use TPR (Total Physical Response) gestures alongside French audio prompts for beginner classes.</small>
        </div>
        """, unsafe_allow_html=True)

# --- PAGE 2: DIFFERENTIATED TASKS & QUIZZES ---
elif nav_choice == "🎯 Differentiated Tasks & Quizzes":
    st.subheader("🎯 Differentiated Student Tasks & Quizzes")
    diff_lang = st.radio("Task Language", ["English 🇬🇧", "Français 🇫🇷"], horizontal=True)
    diff_topic = st.text_input("Topic or Concept", placeholder="e.g., Les articles définis et indéfinis or Fractions")
    diff_grade = st.selectbox("Grade Level", CLASS_LEVELS, key="diff_g")
    
    if st.button("Generate Differentiated Tasks"):
        if diff_topic:
            with st.spinner("Generating multi-tier exercises..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    prompt = f"Generate multi-tier task levels (remedial, core, extension) for {diff_topic}, Grade {diff_grade}. Language: {diff_lang}."
                    res = call_gemini_with_retry(client, prompt)
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# --- PAGE 3: IMPROVISED TLMs & VISUALS ---
elif nav_choice == "🎨 Improvised TLMs & Visuals":
    st.subheader("🎨 Improvised Teaching Materials & Visual Aids")
    tlm_topic = st.text_input("Topic for Visual Aid", placeholder="e.g., Objects in the classroom (Les objets de la classe)")
    
    if st.button("Generate Ideas & Visuals"):
        if tlm_topic:
            with st.spinner("Creating teaching material suggestions..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    res = call_gemini_with_retry(client, f"Provide low-cost/zero-cost local teaching material ideas for teaching {tlm_topic}.")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# --- PAGE 4: FAQ ---
elif nav_choice == "❓ FAQ":
    st.subheader("❓ Frequently Asked Questions")
    with st.expander("Can I generate entire lesson plans in French?"):
        st.write("Yes! Select 'Français 🇫🇷' in the Output Language dropdown on the Lesson Plan Generator tab, and all generated objectives, steps, and assessments will be created in French.")
    with st.expander("How does the Community Context option work?"):
        st.write("Entering details like class size, rural/urban setting, or resource availability instructs the AI to propose activities and materials that match your specific school environment.")
prompt = f"""
                        You are an expert curriculum planner. Generate a comprehensive weekly lesson plan.
                        
                        SETTINGS & CONTEXT:
                        - Target Output Language: {plan_language} ({lang_instruction})
                        - Subject: {subject}
                        - Strand: {strand}
                        - Topic: {topic_input}
                        - Class Level: {grade_level}
                        - Duration: {duration}
                        - Classroom Environment & Community Context: {community_context if community_context else 'Standard classroom setup'}
                        
                        INSTRUCTIONS:
                        1. Structure into 3 clear phases: Starter (Warm-up), Main Learning Activities, and Reflection/Assessment.
                        2. Actively adapt activities and teaching aids to match the provided Community Context and Classroom Environment so it directly fits the learners' daily lives.
                        """
                        
                        res = call_gemini_with_retry(client, prompt)
                        st.session_state["current_plan"] = res.text
                        st.session_state["history"].append({"title": f"{subject}: {topic_input} ({plan_language})"})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Middle Column: Preview & Edit Area
    with col_middle:
        st.markdown("### Lesson Preview & Edit")
        plan_content = st.session_state.get("current_plan", "Select details on the left and click 'Generate Draft' to create your lesson plan preview here.")
        edited_plan = st.text_area("Drafting Area", value=plan_content, height=520)
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            st.button("💾 Save Plan")
        with c_btn2:
            st.button("📤 Export Plan")

    # Right Column: AI Suggestions
    with col_right:
        st.markdown("### AI Suggestions")
        st.markdown("""
        <div class="dashboard-card">
            <strong>💡 Environmental Adaptation</strong><br>
            <small>Incorporating rural or urban community references increases student engagement by up to 40%.</small>
        </div>
        <div class="dashboard-card">
            <strong>🗣️ French Immersion Tip</strong><br>
            <small>Use TPR (Total Physical Response) gestures alongside French audio prompts for beginner classes.</small>
        </div>
        """, unsafe_allow_html=True)

# --- PAGE 2: DIFFERENTIATED TASKS & QUIZZES ---
elif nav_choice == "🎯 Differentiated Tasks & Quizzes":
    st.subheader("🎯 Differentiated Student Tasks & Quizzes")
    diff_lang = st.radio("Task Language", ["English 🇬🇧", "Français 🇫🇷"], horizontal=True)
    diff_topic = st.text_input("Topic or Concept", placeholder="e.g., Les articles définis et indéfinis or Fractions")
    diff_grade = st.selectbox("Grade Level", CLASS_LEVELS, key="diff_g")
    
    if st.button("Generate Differentiated Tasks"):
        if diff_topic:
            with st.spinner("Generating multi-tier exercises..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    prompt = f"Generate multi-tier task levels (remedial, core, extension) for {diff_topic}, Grade {diff_grade}. Language: {diff_lang}."
                    res = call_gemini_with_retry(client, prompt)
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# --- PAGE 3: IMPROVISED TLMs & VISUALS ---
elif nav_choice == "🎨 Improvised TLMs & Visuals":
    st.subheader("🎨 Improvised Teaching Materials & Visual Aids")
    tlm_topic = st.text_input("Topic for Visual Aid", placeholder="e.g., Objects in the classroom (Les objets de la classe)")
    
    if st.button("Generate Ideas & Visuals"):
        if tlm_topic:
            with st.spinner("Creating teaching material suggestions..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    res = call_gemini_with_retry(client, f"Provide low-cost/zero-cost local teaching material ideas for teaching {tlm_topic}.")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# --- PAGE 4: FAQ ---
elif nav_choice == "❓ FAQ":
    st.subheader("❓ Frequently Asked Questions")
    with st.expander("Can I generate entire lesson plans in French?"):
        st.write("Yes! Select 'Français 🇫🇷' in the Output Language dropdown on the Lesson Plan Generator tab, and all generated objectives, steps, and assessments will be created in French.")
    with st.expander("How does the Community Context option work?"):
        st.write("Entering details like class size, rural/urban setting, or resource availability instructs the AI to propose activities and materials that match your specific school environment.")
diff_grade = st.selectbox("Grade Level", CLASS_LEVELS, key="diff_g")
    
    if st.button("Generate Differentiated Tasks"):
        if diff_topic:
            with st.spinner("Generating multi-tier exercises..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    prompt = f"Generate multi-tier task levels (remedial, core, extension) for {diff_topic}, Grade {diff_grade}. Language: {diff_lang}."
                    res = call_gemini_with_retry(client, prompt)
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# --- PAGE 3: IMPROVISED TLMs & VISUALS ---
elif nav_choice == "🎨 Improvised TLMs & Visuals":
    st.subheader("🎨 Improvised Teaching Materials & Visual Aids")
    tlm_topic = st.text_input("Topic for Visual Aid", placeholder="e.g., Objects in the classroom (Les objets de la classe)")
    
    if st.button("Generate Ideas & Visuals"):
        if tlm_topic:
            with st.spinner("Creating teaching material suggestions..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    res = call_gemini_with_retry(client, f"Provide low-cost/zero-cost local teaching material ideas for teaching {tlm_topic}.")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# --- PAGE 4: FAQ ---
elif nav_choice == "❓ FAQ":
    st.subheader("❓ Frequently Asked Questions")
    with st.expander("Can I generate entire lesson plans in French?"):
        st.write("Yes! Select 'Français 🇫🇷' in the Output Language dropdown on the Lesson Plan Generator tab, and all generated objectives, steps, and assessments will be in French.")
    with st.expander("How does the Community Context option work?"):
        st.write("Entering details like class size, rural/urban setting, or resource availability instructs the AI to propose activities and materials that match your specific school environment.")
ture": {
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

CLASS_LEVELS = ["Basic 1", "Basic 2", "Basic 3", "Basic 4", "Basic 5", "Basic 6", "Basic 7 (JHS 1)", "Basic 8 (JHS 2)", "Basic 9 (JHS 3)"]

# MAIN WORKSPACE TABS
tab_plan, tab_diff, tab_tlm, tab_faq = st.tabs([
    "📚 NaCCA Weekly Planner", 
    "🎯 Differentiated Tasks & Quizzes", 
    "🎨 Improvised TLMs & Media Generator",
    "❓ FAQ & Teacher Help"
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
    st.subheader("📅 Weekly Teaching Schedule")
    selected_days = st.multiselect(
        "Select the days you teach this lesson:",
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

# ==========================================
# TAB 2: DIFFERENTIATED TASKS & QUIZZES
# ==========================================
with tab_diff:
    st.subheader("🎯 Differentiated Student Tasks & Quiz Generator")
    st.write("Generate multi-tier learning tasks (Remedial, Standard, Extension) and an end-of-lesson exit quiz.")
    
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
                    Create differentiated classroom tasks and an exit ticket quiz for:
                    - Topic: {diff_topic}
                    - Class Level: {diff_class}
                    """
                    diff_response = call_gemini_with_retry(client, diff_prompt)
                    st.markdown(diff_response.text)
                except Exception as e:
                    st.error(f"Error generating tasks: {str(e)}")

# ==========================================
# TAB 3: IMPROVISED LOCAL TLMS & MEDIA
# ==========================================
with tab_tlm:
    st.subheader("🎨 Improvised Local TLMs & Media Generator")
    st.write("Get zero-cost Ghanaian teaching material ideas and optionally generate classroom charts or PowerPoint slides.")
    
    tlm_topic = st.text_input("Topic for Teaching Aids", placeholder="e.g., Human Digestive System or Separation of Mixtures")
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        gen_image = st.checkbox("🖼️ Generate Printable Chart Image", value=False)
    with col_opt2:
        gen_ppt = st.checkbox("📊 Generate PowerPoint (.pptx)", value=False)
    
    if st.button("💡 Generate Materials & Optional Media"):
        if not tlm_topic:
            st.warning("Please enter a topic.")
        else:
            with st.spinner("My T.A. is preparing your resources..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    tlm_prompt = f"Provide zero-cost Ghanaian TLM ideas for: {tlm_topic}"
                    tlm_response = call_gemini_with_retry(client, tlm_prompt)
                    st.markdown(tlm_response.text)
                    
                    if gen_image:
                        st.markdown("### 🖼️ Generated Classroom Visual Chart")
                        clean_prompt = f"Educational infographic chart for classroom teaching about {tlm_topic}, clear labels, colorful, high quality"
                        image_url = f"https://pollinations.ai/p/{clean_prompt.replace(' ', '%20')}?width=800&height=500&seed=42"
                        st.image(image_url, caption=f"Printable Visual Chart: {tlm_topic}", use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating TLMs: {str(e)}")

 
