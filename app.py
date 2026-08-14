import io
import time
from datetime import datetime
from google import genai
import streamlit as st

# Optional ReportLab PDF engine check
try:
  from reportlab.lib import colors
  from reportlab.lib.pagesizes import letter
  from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
  from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

  HAS_REPORTLAB = True
except ImportError:
  HAS_REPORTLAB = False

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="PlanAhead: AI Lesson Wizard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 2. RESPONSIVE CSS STYLING
# ==========================================
st.markdown(
    """
<style>
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
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
          model="gemini-3.6-flash", contents=prompt
      )
    except Exception as e:
      if (
          "503" in str(e) or "UNAVAILABLE" in str(e)
      ) and attempt < max_retries - 1:
        time.sleep(2)
        continue
      else:
        raise e


def create_valid_pdf(text_content):
  """Generates a PDF document supporting tables and headers."""
  buffer = io.BytesIO()

  if HAS_REPORTLAB:
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        spaceAfter=4,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=4,
        textColor="#0284C7",
    )

    elements = []
    lines = text_content.split("\n")

    in_table = False
    table_data = []

    for line in lines:
      clean_line = line.strip()
      if not clean_line:
        if in_table and table_data:
          t = Table(table_data, colWidths=[110, 290, 140])
          t.setStyle(
              TableStyle([
                  ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284C7")),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                  ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                  ("FONTSIZE", (0, 0), (-1, 0), 9),
                  ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                  ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                  ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                  ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ])
          )
          elements.append(t)
          elements.append(Spacer(1, 10))
          table_data = []
          in_table = False
        continue

      if "|" in clean_line:
        # Table row parsing
        row = [
            Paragraph(cell.strip().replace("*", ""), normal_style)
            for cell in clean_line.split("|")[1:-1]
        ]
        if row and not all("---" in cell for cell in clean_line.split("|")[1:-1]):
          table_data.append(row)
          in_table = True
      else:
        if in_table and table_data:
          t = Table(table_data, colWidths=[110, 290, 140])
          t.setStyle(
              TableStyle([
                  ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284C7")),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                  ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                  ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                  ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ])
          )
          elements.append(t)
          elements.append(Spacer(1, 10))
          table_data = []
          in_table = False

        safe_text = (
            clean_line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        if clean_line.startswith("#") or clean_line.startswith("**"):
          clean_heading = (
              safe_text.replace("#", "").replace("*", "").strip()
          )
          elements.append(Paragraph(f"<b>{clean_heading}</b>", heading_style))
        else:
          clean_text = safe_text.replace("*", "")
          elements.append(Paragraph(clean_text, normal_style))

    if in_table and table_data:
      t = Table(table_data, colWidths=[110, 290, 140])
      t.setStyle(
          TableStyle([
              ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284C7")),
              ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
              ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
              ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ])
      )
      elements.append(t)

    doc.build(elements)
  else:
    # Standard stream fallback
    lines = text_content.split("\n")
    pdf_lines = ["%PDF-1.4"]
    pdf_lines.append("1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj")
    pdf_lines.append("2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj")
    pdf_lines.append(
        "3 0 obj <</Type /Page /Parent 2 0 R /Resources <</Font <</F1 4 0"
        " R>>>> /MediaBox [0 0 612 792] /Contents 5 0 R>> endobj"
    )
    pdf_lines.append(
        "4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj"
    )

    stream_content = "BT /F1 9 Tf 36 750 Td 12 TL\n"
    for line in lines[:55]:
      clean = (
          line.replace("(", "\\(")
          .replace(")", "\\)")
          .replace("*", "")
          .replace("#", "")
      )
      stream_content += f"({clean[:85]}) '\n"
    stream_content += "ET"

    pdf_lines.append(
        f"5 0 obj <</Length {len(stream_content)}>>\nstream\n{stream_content}\nendstream\nendobj"
    )

    xref_offset = sum(len(s) + 1 for s in pdf_lines)
    pdf_lines.append(
        f"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000"
        " n \n0000000111 00000 n \n0000000224 00000 n \n0000000293 00000 n"
        f" \ntrailer <</Size 6 /Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF"
    )

    buffer.write("\n".join(pdf_lines).encode("latin-1", errors="replace"))

  buffer.seek(0)
  return buffer


# ==========================================
# 4. MASTER CURRICULUM DATA
# ==========================================
CURRICULUM_DATA = {
    "Standard Base-Curriculum (Basic 1 - 6)": {
        "French Language": {
            "Oral Expression & Comprehension": [
                "Greetings & Self-Introduction",
                "School & Family Vocabulary",
                "Daily Directives & Polite Expressions",
            ],
            "Reading Comprehension": [
                "Simple Texts & Dialogues",
                "Vocabulary Building & Word Recognition",
            ],
            "Written Expression": [
                "Short Sentences & Descriptions",
                "Basic Grammar & Conjugation",
            ],
        },
        "Mathematics": {
            "Number": [
                "Counting, Representation & Cardinality",
                "Whole Numbers, Place Value & Operations",
                "Fractions, Decimals & Percentages",
            ],
            "Algebra": [
                "Patterns & Relationships",
                "Simple Equations & Expressions",
            ],
            "Geometry & Measurement": [
                "Lines, 2D Shapes & 3D Objects",
                "Perimeter, Area & Volume",
            ],
            "Data": ["Data Collection, Organization & Presentation"],
        },
        "Science": {
            "Diversity of Matter": [
                "Living and Non-Living Things",
                "Materials & Mixtures",
            ],
            "Cycles": ["Earth Science & Weather", "Life Cycles of Organisms"],
            "Systems": ["Human Body Systems", "Plant Systems", "Ecosystems"],
            "Forces & Energy": [
                "Sources & Forms of Energy",
                "Simple Machines & Motion",
            ],
        },
        "English Language": {
            "Oral Language": ["Listening & Speaking", "Pronunciation & Rhymes"],
            "Reading": ["Phonics & Vocabulary", "Comprehension Strategies"],
            "Writing": [
                "Penmanship & Mechanics",
                "Creative Writing & Composition",
                "Grammar & Usage",
            ],
        },
    },
    "Common Core Programme (CCP) (Basic 7 - 9 / JHS 1 - 3)": {
        "French Language (CCP)": {
            "Compréhension Orale": [
                "Écouter et comprendre des messages oraux",
                "Dialogues et interactions sociales",
            ],
            "Production Orale": [
                "S'exprimer sur des sujets familiers",
                "Exposés et présentations simples",
            ],
            "Compréhension Écrite": [
                "Lecture et analyse de textes court",
                "Identification d'informations spécifiques",
            ],
            "Production Écrite": [
                "Rédaction de courts paragraphes",
                "Correspondance et messages formels/informels",
            ],
        },
        "Mathematics (CCP)": {
            "Number": [
                "Real Number System & Operations",
                "Ratios, Rates & Proportions",
                "Financial Mathematics",
            ],
            "Algebra": [
                "Algebraic Expressions & Operations",
                "Linear Equations & Inequalities",
                "Functions & Graphs",
            ],
            "Geometry & Measurement": [
                "Geometric Constructions",
                "Trigonometry & Bearing",
                "Mensuration & Transformations",
            ],
            "Handling Data": [
                "Data Collection & Presentation",
                "Data Analysis & Measures of Central Tendency",
                "Probability",
            ],
        },
        "Science (CCP)": {
            "Diversity of Matter": [
                "Structure of Matter & Atom",
                "Elements, Compounds & Mixtures",
                "Chemical Reactions",
            ],
            "Cycles": [
                "Earth & Space Science",
                "Life Processes & Biogeochemical Cycles",
            ],
            "Systems": [
                "Human Body Systems & Health",
                "Ecosystems & Ecological Interactions",
            ],
            "Forces & Energy": [
                "Energy Transformations & Conservation",
                "Electricity & Magnetism",
                "Forces, Work & Motion",
            ],
        },
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
DAYS_OPTIONS = [
    "All Days (Full Week)",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
]

# ==========================================
# 5. LOGIN SCREEN
# ==========================================
if not st.session_state["authenticated"]:
  st.markdown(
      "<h2 style='text-align: center;'>🔐 PlanAhead Teacher Portal Login</h2>",
      unsafe_allow_html=True,
  )
  col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
  with col_l2:
    teacher_name = st.text_input(
        "👤 Teacher Name", placeholder="e.g. Mr. Mensah"
    )
    api_key_input = st.text_input(
        "🔑 Gemini API Key", type="password", placeholder="Paste API key here..."
    )
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

  nav_choice = st.radio(
      "NAVIGATION",
      [
          "📝 Lesson Plan Generator",
          "🎯 Differentiated Tasks & Quizzes",
          "🎨 Improvised TLMs & Visuals",
      ],
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
st.markdown(
    f"""
<div class="top-navbar">
    <div class="brand-title">📘 PlanAhead: AI Lesson Wizard</div>
    <div class="user-profile">👤 {st.session_state['teacher_name']}</div>
</div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 8. MAIN CONTENT ROUTING
# ==========================================

if nav_choice == "📝 Lesson Plan Generator":

  st.markdown("### Step 1: Lesson Details")

  col_1, col_2 = st.columns(2)

  with col_1:
    plan_language = st.selectbox(
        "🌐 Output Language",
        [
            "English ",
            "French",
        ],
    )

    grade_level = st.selectbox("Grade Level", CLASS_LEVELS)

    if (
        "Basic 7" in grade_level
        or "Basic 8" in grade_level
        or "Basic 9" in grade_level
    ):
      programme_type = "Common Core Programme (CCP) (Basic 7 - 9 / JHS 1 - 3)"
      st.info("📋 Framework: Common Core Programme (CCP)")
    else:
      programme_type = "Standard Base-Curriculum (Basic 1 - 6)"
      st.info("📋 Framework: Standard Base-Curriculum")

    subject = st.selectbox(
        "Subject", list(CURRICULUM_DATA[programme_type].keys())
    )

    strands_list = list(CURRICULUM_DATA[programme_type][subject].keys())
    strand = st.selectbox("Strand", strands_list)

  with col_2:
    sub_strands_list = CURRICULUM_DATA[programme_type][subject][strand]
    sub_strand = st.selectbox("Sub-strand", sub_strands_list)

    topic_input = st.text_input(
        "Topic", value="Se présenter et saluer / Greetings"
    )

    selected_days = st.multiselect(
        "📅 Select Day(s)", DAYS_OPTIONS, default=["All Days (Full Week)"]
    )

    duration = st.selectbox(
        "Duration per session", ["30 min", "45 min", "60 min", "90 min"]
    )

  st.markdown("### 🏡 Context & Environment")
  community_context = st.text_area(
      "Classroom & Community Context",
      placeholder=(
          "Describe class environment or community (e.g., Rural farming area,"
          " 50+ students, mixed ability, limited electricity)."
      ),
      height=80,
  )

  if st.button("🚀 Generate Draft"):
    if topic_input:
      if not selected_days:
        st.error("Please select at least one day or 'All Days'.")
      else:
        with st.spinner("Generating customized lesson plan in table format..."):
          try:
            client = genai.Client(api_key=st.session_state["api_key"])
            lang_instruction = (
                "Write the ENTIRE lesson plan strictly in FRENCH language."
                if "Français" in plan_language
                else "Write the lesson plan in English."
            )

            days_formatted = (
                "All Days (Monday to Friday)"
                if "All Days (Full Week)" in selected_days
                else ", ".join(selected_days)
            )

            prompt = f"""
                        You are an expert curriculum planner. Generate a comprehensive lesson plan in a STRICT TABLE FORMAT.
                        
                        SETTINGS & CONTEXT:
                        - Curriculum Framework: {programme_type}
                        - Target Output Language: {plan_language} ({lang_instruction})
                        - Subject: {subject}
                        - Strand: {strand}
                        - Sub-strand: {sub_strand}
                        - Topic: {topic_input}
                        - Class Level: {grade_level}
                        - Target Day(s): {days_formatted}
                        - Duration per session: {duration}
                        - Classroom Environment: {community_context if community_context else 'Standard classroom setup'}
                        
                        OUTPUT STRUCTURE REQUIREMENT:
                        Start with a Header block listing Class Level, Subject, Strand, Sub-strand, Duration, and Day(s).
                        
                        Then, for each requested day, output the lesson plan inside a Markdown Table with the following 3 exact columns:
                        | Phase / Duration | Teacher & Learner Activities | TLMs & Assessment |
                        | --- | --- | --- |
                        | Phase 1: Starter (10 min) | [Detailed step-by-step warm-up activity] | [Resources & diagnostic assessment] |
                        | Phase 2: Main Learning (30 min) | [Detailed step-by-step main activity] | [Visual aids & core assessment] |
                        | Phase 3: Reflection / Closure (10 min) | [Plenary & summary activities] | [Evaluation & home task] |
                        
                        Actively adapt activities and teaching aids to match the provided Community Context and Classroom Environment.
                        """

            res = call_gemini_with_retry(client, prompt)
            st.session_state["current_plan"] = res.text
            st.session_state["history"].append(
                {"title": f"{subject}: {topic_input} ({days_formatted})"}
            )
          except Exception as e:
            st.error(f"Error: {str(e)}")

  st.divider()

  # --- BOTTOM SECTION: LESSON PREVIEW & EDIT ---
  st.markdown("### 📄 Lesson Preview & Edit")
  plan_content = st.session_state.get(
      "current_plan",
      "Fill in the details above and click 'Generate Draft' to create your"
      " lesson plan in table format here.",
  )
        # --- Export Options ---
    st.markdown("### 📥 Export Options")
    
    btn_c1, btn_c2 = st.columns(2)

    with btn_c1:
        pdf_buffer = create_valid_pdf(edited_plan)
        st.download_button(
            label="📥 Download as PDF Table",
            data=pdf_buffer,
            file_name=f"Lesson_Plan_{subject}_{grade_level}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with btn_c2:
        st.download_button(
            label="📝 Download as Word Doc (.doc)",
            data=edited_plan,
            file_name=f"Lesson_Plan_{subject}_{grade_level}.doc",
            mime="application/msword",
            use_container_width=True
        )

  
