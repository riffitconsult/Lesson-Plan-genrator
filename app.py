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
    page_title="NaCCA Lesson Plan Generator",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Ghanaian Curriculum (NaCCA) Lesson Plan Generator")
st.write("Generate weekly structured lesson plans in printable table format.")

# 2. Sidebar for Setup
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key:", type="password")
    st.markdown("[Get a free Gemini API Key](https://aistudio.google.com/)")
    
    st.divider()
    st.markdown("### Features")
    st.markdown("- **Dynamic Dropdowns:** Strands & Sub-strands auto-adjust per subject")
    st.markdown("- **Smart AI Generation:** TLMs & Core Competencies generated automatically")
    st.markdown("- **Custom Days:** Pick specific teaching days (Mon, Wed, Fri)")
    st.markdown("- **Export Formats:** Download directly as PDF Table or Word document")

# Helper function to generate Word document
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

# Helper function to convert raw HTML string into PDF
def create_pdf(html_code):
    buffer = io.BytesIO()
    HTML(string=html_code).write_pdf(target=buffer)
    buffer.seek(0)
    return buffer

# 3. Curriculum Data Dictionary for Dependent Dropdowns
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

# Standard Indicator Mapping based on selected class
CLASS_LEVELS = ["Basic 1", "Basic 2", "Basic 3", "Basic 4", "Basic 5", "Basic 6", "Basic 7 (JHS 1)", "Basic 8 (JHS 2)", "Basic 9 (JHS 3)"]

# Form Layout
col1, col2, col3 = st.columns(3)

with col1:
    class_level = st.selectbox("Class Level", CLASS_LEVELS)
    subject = st.selectbox("Subject", list(CURRICULUM_DATA.keys()))
    
    # Dependent Strand dropdown based on Subject
    available_strands = list(CURRICULUM_DATA[subject].keys())
    strand = st.selectbox("Strand", available_strands)

with col2:
    # Dependent Sub-strand dropdown based on Strand
    available_substrands = CURRICULUM_DATA[subject][strand]
    sub_strand = st.selectbox("Sub-Strand", available_substrands)
    
    # Class code prefix extraction (e.g. Basic 4 -> B4)
    code_prefix = "B" + class_level.split(" ")[1] if "Basic" in class_level else "B7"
    
    content_standard = st.selectbox(
        "Content Standard Code", 
        [f"{code_prefix}.1.1", f"{code_prefix}.1.2", f"{code_prefix}.2.1", f"{code_prefix}.2.2", f"{code_prefix}.3.1"]
    )
    
    indicator_code = st.selectbox(
        "Indicator Code", 
        [f"{content_standard}.1", f"{content_standard}.2", f"{content_standard}.3"]
    )

with col3:
    # Selected teaching days
    selected_days = st.multiselect(
        "Teaching Days (Pick days for this week)",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        default=["Monday", "Wednesday", "Friday"]
    )
    
    duration = st.selectbox("Duration per Session", ["30 mins", "45 mins", "60 mins", "70 mins", "90 mins", "100 mins (Double Period)"])
    class_size = st.text_input("Class Size (Optional)", value="40 pupils")

topic = st.text_area("Lesson Topic & Specific Learning Objectives", placeholder="e.g., Identify equivalent fractions using paper folding activities.")

# 4. Action Button & Execution
if st.button("🚀 Generate Lesson Plan Table", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
    elif not topic:
        st.warning("⚠️ Please fill in the Lesson Topic & Learning Objectives.")
    elif len(selected_days) == 0:
        st.warning("⚠️ Please select at least one teaching day.")
    else:
        with st.spinner("Analyzing curriculum standards and writing your lesson plan..."):
            try:
                client = genai.Client(api_key=api_key)
                
                days_list_str = ", ".join(selected_days)
                num_lessons = len(selected_days)
                
                # Dynamic system prompt forcing Gemini to infer TLMs, Core Competencies, and format table across chosen days
                prompt = f"""
                You are an expert curriculum developer specializing in the Ghanaian NaCCA standard curriculum.
                Generate a complete, professionally formatted weekly lesson plan inside a single self-contained HTML document using styled <table> tags.

                INPUT DETAILS:
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
                1. Return ONLY pure HTML code inside an <html><body> tag. Do NOT wrap it in Markdown code blocks (no ```html).
                2. Include CSS styling for clean, professional PDF printing (border-collapse, clean blue header banner `#1a365d`, padding, clear borders `#cbd5e0`, A4 page layout).
                3. Top Header Metadata Table: Include Subject, Class, Strand, Sub-strand, Duration, Content Standard, Indicator Code, Core Competencies, and TLMs.
                4. Schedule Table: Generate exactly {num_lessons} separate lesson sections corresponding to the selected days: {days_list_str}.
                5. Structure each day's lesson into the 3 mandatory NaCCA phases:
                   - PHASE 1: STARTER (Preparing the brain / revision - 10 mins)
                   - PHASE 2: NEW LEARNING / MAIN (Step-by-step learner activities, group work, and inline assessment questions)
                   - PHASE 3: REFLECTION / PLENARY (Learner feedback & summary)
                6. Add a Teacher Evaluation & Remarks box at the bottom.
                """

                # Calling Gemini API
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                raw_html = response.text.replace("```html", "").replace("```", "").strip()
                
                st.success(f"✅ Generated {num_lessons}-Day Lesson Plan ({days_list_str}) Successfully!")
                
                # Render the clean HTML table view directly in Streamlit
                st.components.v1.html(raw_html, height=800, scrolling=True)
                
                # Download Buttons
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
                        st.warning("PDF engine loading... Please use Word download below.")

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
