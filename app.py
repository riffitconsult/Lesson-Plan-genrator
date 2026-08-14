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

    /* Top Navigation Header Bar */
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #FFFFFF;
        padding: 14px 24px;
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

    /* Custom Dashboard Card */
    .dashboard-card {
        background-color: #FFFFFF;
        padding: 18px;
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
    "Standard Base-Curriculum (Basic 1 - 6)": {
        "French Language": {
            "Oral Expression & Comprehension": ["Greetings & Self-Introduction", "School & Family Vocabulary", "Daily Directives"],
            "Reading Comprehension": ["Simple Texts & Dialogues", "Vocabulary Building"],
            "Written Expression": ["Short Sentences & Descriptions", "Grammar & Conjugation"]
        },
        "Mathematics": {
            "Number": ["Whole Numbers, Place Value & Operations", "Fractions, Decimals & Percentages"],
            "Algebra": ["Patterns & Relationships", "Simple Equations"],
            "Geometry & Measurement": ["Lines, Shapes & 3D Objects", "Perimeter, Area & Volume"],
            "Data": ["Data Collection & Presentation"]
        },
        "Science": {
            "Diversity of Matter": ["Living and Non-Living Things", "Materials & Mixtures"],
            "Cycles": ["Earth Science & Weather", "Life Cycles of Organisms"],
            "Systems": ["Human Body Systems", "Plant Systems", "Ecosystems"],
            "Forces & Energy": ["Sources of Energy", "Simple Machines"]
        },
        "English Language": {
            "Oral Language": ["Listening & Speaking", "Pronunciation & Rhymes"],
            "Reading": ["Phonics & Vocabulary", "Comprehension"],
            "Writing": ["Penmanship", "Creative Writing", "Grammar"]
        },
        "Our World Our People (OWOP)": {
            "All About Us": ["Nature of God", "Self & Family"],
            "All Around Us": ["Environment", "Plants & Animals"],
            "Our Beliefs & Values": ["Moral Values", "Cultural Diversity"]
        },
        "Religious & Moral Education (RME)": {
            "God, Creation & Attributes": ["Creator & Environment"],
            "Religious Practices": ["Prayer & Worship"],
            "Moral Life": ["Honesty & Good Manners"]
        },
        "Creative Arts": {
            "Visual Arts": ["Drawing & Painting", "Crafts & Modelling"],
            "Performing Arts": ["Music & Dance", "Drama & Storytelling"]
        }
    },
    "Common Core Programme (CCP) (Basic 7 - 9 / JHS 1 - 3)": {
        "French Language (CCP)": {
            "Compréhension Orale": ["Écouter et comprendre des messages oraux", "Dialogues et interactions"],
            "Production Orale": ["S'exprimer sur des sujets familiers", "Exposés simples"],
            "Compréhension Écrite": ["Lecture et analyse de textes simples", "Identification d'informations"],
            "Production Écrite": ["Rédaction de courts paragraphes", "Correspondance et messages"]
        },
        "Mathematics (CCP)": {
            "Number": ["Real Number System", "Ratios, Rates & Proportions", "Financial Mathematics"],
            "Algebra": ["Algebraic Expressions", "Linear Equations & Inequalities", "Functions & Graphs"],
            "Geometry & Measurement": ["Geometric Constructions", "Trigonometry & Bearing", "Mensuration"],
            "Handling Data": ["Data Collection & Presentation", "Data Analysis", "Probability"]
        },
        "Science (CCP)": {
            "Diversity of Matter": ["Structure of Matter", "Elements, Compounds & Mixtures", "Chemical Reactions"],
            "Cycles": ["Earth & Space Science", "Life Processes & Cycles"],
            "Systems": ["Human Body Systems", "Ecosystems & Interactions"],
            "Forces & Energy": ["Energy Transformations", "Electricity & Magnetism", "Forces & Motion"]
        },
        "English Language (CCP)": {
            "Oral Language": ["Listening Comprehension", "Speaking & Presentation"],
            "Reading": ["Reading Comprehension", "Literary Appreciation"],
            "Writing": ["Expository & Narrative Essays", "Formal & Informal Letters"],
            "Language Conventions": ["Grammar", "Punctuation & Vocabulary"]
        },
        "Social Studies (CCP)": {
            "Environment": ["Physical Environment", "Environmental Degradation & Conservation"],
            "Governance, Politics & Stability": ["Citizenship & Governance", "Peace & Conflict Resolution"],
            "Social & Economic Development": ["Socio-Economic Infrastructure", "Population & Resources"]
        },
        "Career Technology (CCP)": {
            "Health & Safety": ["Personal & Workshop Safety", "Food Hygiene & Sanitation"],
            "Materials for Production": ["Wood, Metal & Plastics", "Food Commodities"],
            "Tools & Equipment": ["Measuring & Marking Out Tools", "Processing Tools"],
            "Designing & Making": ["Design Process & Drawing", "Prototyping"]
        },
        "Computing (CCP)": {
            "Introduction to Computing": ["Hardware Components", "Operating Systems & File Management"],
            "Productivity Software": ["Word Processing", "Spreadsheet Applications", "Presentations"],
            "Communication & Web": ["Internet & Web Browsing", "Cybersecurity & Ethics"],
            "Computational Thinking": ["Algorithms & Basic Programming"]
        },
        "Religious & Moral Education (CCP)": {
            "God, His Creation & Attributes": ["Attributes of God", "Stewardship of the Earth"],
            "Religious Practices & Personalities": ["Religious Leaders", "Festivals & Rites"],
            "Ethics, Manners & Family": ["Moral Values & Character", "Family Roles & Social Responsibility"]
        },
        "Creative Arts & Design (CCP)": {
            "Design": ["Design Process & Technical Drawing"],
            "Visual Arts": ["2D & 3D Artwork", "Local Crafts"],
            "Performing Arts": ["Music Composition & Performance", "Dance & Theatre"]
        }
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
# 6. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("### 📘 **PlanAhead**")
    st.caption(f"Logged in: {st.session_state['teacher_name']}")
    st.divider()

    # Core navigation options (FAQ removed)
    nav_choice = st.radio(
        "NAVIGATION",
        [
            "📝 Lesson Plan Generator",
            "🎯 Differentiated Tasks & Quizzes",
            "🎨 Improvised TLMs & Visuals"
        ]
    )

    st.divider()
    st.markdown("### 🕒 **Recent Plans**")
    if len(st.session_state["history"]) == 0:
        st.caption("• French (CCP Basic 8) - Dialogues")
        st.caption("• Science (Base Basic 5) - Ecosystems")
    else:
        for item in st.session_state["history"][-5:]:
            st.caption(f"• {item['title']}")

    st.divider()
    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

# ==========================================
# 7. HEADER NAVBAR
# ==========================================
st.markdown(f"""
<div class="top-navbar">
    <div class="brand-title">📘 PlanAhead: AI Lesson Wizard</div>
    <div class="user-profile">👤 {st.session_state['teacher_name']}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 8. MAIN CONTENT ROUTING
# ==========================================

# --- PAGE 1: LESSON PLAN GENERATOR ---
if nav_choice == "📝 Lesson Plan Generator":
    
    col_left, col_middle, col_right = st.columns([1.2, 1.5, 1])

    with col_left:
        st.markdown("### Step 1: Lesson Details")
        
        plan_language = st.selectbox(
            "🌐 Output Language", 
            ["English 🇬🇧", "Français 🇫🇷 (French)", "English with French Terminology"]
        )

        grade_level = st.selectbox("Grade Level", CLASS_LEVELS)
        
        # Dynamically switch between Base-Curriculum and CCP based on Grade
        if "Basic 7" in grade_level or "Basic 8" in grade_level or "Basic 9" in grade_level:
            programme_type = "Common Core Programme (CCP) (Basic 7 - 9 / JHS 1 - 3)"
            st.info("📋 Framework: Common Core Programme (CCP)")
        else:
            programme_type = "Standard Base-Curriculum (Basic 1 - 6)"
            st.info("📋 Framework: Standard Base-Curriculum")

        subject = st.selectbox("Subject", list(CURRICULUM_DATA[programme_type].keys()))
        strand = st.selectbox("Strand", list(CURRICULUM_DATA[programme_type][subject].keys()))
        topic_input = st.text_input("Topic", value="Se présenter et saluer / Greetings")
        duration = st.selectbox("Duration", ["30 min", "45 min", "60 min", "90 min"])

        st.markdown("---")
        st.markdown("### 🏡 Context & Environment")
        community_context = st.text_area(
            "Classroom & Community Context",
            placeholder="Describe class environment or community (e.g., Rural farming area, 50+ students, mixed ability, limited electricity).",
            height=90
        )
        
        if st.button("🚀 Generate Draft"):
            if topic_input:
                with st.spinner("Generating customized lesson plan..."):
                    try:
                        client = genai.Client(api_key=st.session_state["api_key"])
                        lang_instruction = "Write the ENTIRE lesson plan strictly in FRENCH language." if "Français" in plan_language else "Write the lesson plan in English."
                        
                        prompt = f"""
                        You are an expert curriculum planner. Generate a comprehensive lesson plan.
                        
                        SETTINGS & CONTEXT:
                        - Curriculum Type: {programme_type}
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

    with col_middle:
        st.markdown("### Lesson Preview & Edit")
        plan_content = st.session_state.get("current_plan", "Select details on the left and click 'Generate Draft' to create your lesson plan preview here.")
        edited_plan = st.text_area("Drafting Area", value=plan_content, height=520)
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            st.button("💾 Save Plan")
        with c_btn2:
            st.button("📤 Export Plan")

    with col_right:
        st.markdown("### AI Suggestions")
        st.markdown("""
        <div class="dashboard-card">
            <strong>💡 Community Context</strong><br>
            <small>Lessons tailored to the learners' local community improve comprehension and real-world application.</small>
        </div>
        <div class="dashboard-card">
            <strong>🗣️ French Immersion Tip</strong><br>
            <small>Use TPR (Total Physical Response) gestures alongside French spoken instructions for beginner classes.</small>
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
                    prompt = f"Provide low-cost/zero-cost local teaching material ideas for teaching {tlm_topic}."
                    res = call_gemini_with_retry(client, prompt)
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
