import streamlit as st
from google import genai
from docx import Document
import io

# Try importing WeasyPrint for PDF export; handle if missing during setup
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
    st.markdown("- Supports **Basic 1-6** & **Basic 7-9 (JHS)** layouts")
    st.markdown("- Flexible number of weekly lessons (2 to 5 days)")
    st.markdown("- Customizable durations (30m, 45m, 60m, 100m)")
    st.markdown("- Export directly to **PDF Table** or **Word Document**")

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

# 3. Form Inputs
col1, col2, col3 = st.columns(3)

with col1:
    class_level = st.selectbox(
        "Class Level", 
        ["Basic 1", "Basic 2", "Basic 3", "Basic 4", "Basic 5", "Basic 6", "Basic 7 (JHS 1)", "Basic 8 (JHS 2)", "Basic 9 (JHS 3)"]
    )
    subject = st.selectbox(
        "Subject", 
        ["Mathematics", "English Language", "Science", "Social Studies", "Computing", "Creative Arts", "Career Technology", "RME"]
    )
    strand = st.text_input("Strand", placeholder="e.g., Diversity of Matter / Number")

with col2:
    sub_strand = st.text_input("Sub-Strand", placeholder="e.g., Mixtures / Fractions")
    content_standard = st.text_input("Content Standard Code", placeholder="e.g., B8.1.1.1 or B4.1.1.1")
    indicator_code = st.text_input("Indicator Code", placeholder="e.g., B8.1.1.1.1")

with col3:
    num_lessons = st.selectbox("Number of Lessons / Days this week", ["2 Lessons", "3 Lessons", "4 Lessons", "5 Lessons (Mon-Fri)"])
    duration = st.selectbox("Duration per Lesson", ["30 mins", "45 mins", "60 mins", "70 mins", "90 mins", "100 mins (Double Period)"])
    class_size = st.text_input("Class Size (Optional)", placeholder="e.g., 45 pupils")

topic = st.text_area("Lesson Topic & Learning Objectives", placeholder="e.g., Identify types of mixtures by name and characteristics.")

# Resources & Core Competencies
col_res1, col_res2 = st.columns(2)
with col_res1:
    resources = st.text_input("Teaching & Learning Resources (TLMs)", placeholder="e.g., Salt, water, glass containers, charts")
with col_res2:
    core_competencies = st.text_input("Core Competencies", placeholder="e.g., Critical Thinking, Collaboration, Communication, Digital Literacy")

# 4. Action Button & API Call
if st.button("🚀 Generate Lesson Plan Table", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
    elif not topic or not strand:
        st.warning("⚠️ Please fill in at least the Topic and Strand.")
    else:
        with st.spinner("Building your weekly lesson plan tables..."):
            try:
                client = genai.Client(api_key=api_key)
                
                # Dynamic system instructions enforcing HTML table output matching Ghanaian NaCCA standards
                prompt = f"""
                You are an expert curriculum developer specializing in the Ghanaian NaCCA standard curriculum.
                Generate a complete, professionally formatted weekly lesson plan inside a single self-contained HTML file (using styled <table> tags).

                INPUT DETAILS:
                - Class Level: {class_level}
                - Subject: {subject}
                - Strand: {strand}
                - Sub-Strand: {sub_strand}
                - Content Standard: {content_standard}
                - Indicator Code: {indicator_code}
                - Duration per Lesson: {duration}
                - Number of Lessons/Days: {num_lessons}
                - Class Size: {class_size}
                - Topic Details: {topic}
                - TLMs / Resources: {resources}
                - Core Competencies: {core_competencies}

                OUTPUT FORMAT RULES:
                1. Return ONLY pure HTML code inside an <html><body> tag. Do NOT wrap it in Markdown code blocks (no ```html).
                2. Include CSS styling for clean, professional PDF printing (border-collapse, clean blue header banner `#1a365d`, padding, clear borders `#cbd5e0`, A4 page layout).
                3. Top Metadata Table: Include Subject, Class, Strand, Sub-strand, Duration, Indicator, Performance Indicator, Core Competencies, and TLMs.
                4. Schedule Table: Generate exactly {num_lessons} separate lesson sections (e.g., Day 1/Lesson 1, Day 2/Lesson 2 up to the requested number of lessons).
                5. Structure each lesson into 3 mandatory NaCCA phases:
                   - PHASE 1: STARTER (Preparing the brain / revision)
                   - PHASE 2: NEW LEARNING / MAIN (Step-by-step learner activities & group tasks + assessment questions)
                   - PHASE 3: REFLECTION / PLENARY (Learner feedback & summary)
                6. Add a Teacher Evaluation & Remarks box at the bottom.
                """

                # Calling Gemini API using gemini-2.5-flash
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                raw_html = response.text.replace("```html", "").replace("```", "").strip()
                
                st.success("✅ Lesson Plan Generated Successfully!")
                
                # Render the clean HTML table view directly in Streamlit
                st.components.v1.html(raw_html, height=800, scrolling=True)
                
                # Export Options
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
                        st.warning("PDF engine loading... Please click Word Download below.")

                with col_down2:
                    # Provide Word export
                    docx_file = create_docx(topic, f"{subject} - {topic} Lesson Plan")
                    st.download_button(
                        label="📥 Download Word Document (.docx)",
                        data=docx_file,
                        file_name=f"Lesson_Plan_{class_level}_{subject}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

            except Exception as e:
                st.error(f"Error generating lesson plan: {str(e)}")
