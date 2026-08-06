import streamlit as st
from google import genai
from docx import Document
import io

# 1. Page Configuration
st.set_page_config(
    page_title="Lesson Plan Generator",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Lesson Plan Generator")
st.write("Fill in the details below to instantly generate a structured lesson plan.")

# 2. Sidebar Setup
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key:", type="password")
    st.markdown("[Get a free Gemini API Key](https://aistudio.google.com/)")

# Document Creator Helper
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

# 3. Form Layout
col1, col2 = st.columns(2)

with col1:
    class_level = st.selectbox("Class Level", ["Basic 1", "Basic 2", "Basic 3", "Basic 4", "Basic 5", "Basic 6", "Basic 7 (JHS 1)", "Basic 8 (JHS 2)", "Basic 9 (JHS 3)"])
    subject = st.selectbox("Subject", ["Mathematics", "English Language", "Science", "Social Studies", "Computing", "Creative Arts"])
    strand = st.text_input("Strand", placeholder="e.g., Number")

with col2:
    sub_strand = st.text_input("Sub-Strand", placeholder="e.g., Whole Numbers")
    content_standard = st.text_input("Indicator / Content Standard Code", placeholder="e.g., B4.1.1.1")
    duration = st.selectbox("Duration", ["Single Lesson (60 mins)", "Weekly Plan (Mon-Fri)"])

topic = st.text_area("Lesson Topic & Specific Objectives", placeholder="e.g., Place value up to 10,000 and simple additions.")

# 4. Generate Action
if st.button("🚀 Generate Lesson Plan", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
    elif not topic or not strand:
        st.warning("⚠️ Please fill in at least the Topic and Strand.")
    else:
        with st.spinner("Generating lesson plan..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt = f"""
                Act as an expert curriculum developer. Generate a detailed, practical lesson plan:

                - Class: {class_level}
                - Subject: {subject}
                - Duration: {duration}
                - Strand: {strand}
                - Sub-Strand: {sub_strand}
                - Indicator Code: {content_standard}
                - Topic: {topic}

                Output clearly in Markdown format with standard teaching phases:
                1. Header Info
                2. Core Competencies & Performance Indicators
                3. TLMs (Teaching Materials)
                4. Phase 1: Starter / Warm-Up
                5. Phase 2: Main Activities (Step-by-step)
                6. Phase 3: Plenary / Assessment Questions
                """

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                plan_text = response.text
                st.success("✅ Lesson Plan Generated!")
                st.markdown("---")
                st.markdown(plan_text)
                st.markdown("---")
                
                docx_file = create_docx(plan_text, f"{subject} - {topic} Lesson Plan")
                st.download_button(
                    label="📥 Download as Word Document (.docx)",
                    data=docx_file,
                    file_name=f"Lesson_Plan_{class_level}_{subject}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            except Exception as e:
                st.error(f"Error: {str(e)}")
