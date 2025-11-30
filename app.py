import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

# 1. Load API Key
load_dotenv()
genai.configure(api_key=os.getenv("AIzaSyAb2zDHW943NWCACFxQ2BPJIzvwi3WJgeE"))

# 2. Gemini Response Function
def get_gemini_response(input_prompt):
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(input_prompt)
    return response.text

# 3. PDF Reader Function
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

# --- PAGE SETUP ---
st.set_page_config(page_title="Smart ATS Pro", page_icon="🏢", layout="wide")

# --- SIDEBAR: JOB PROFILE MANAGER (NEW!) ---
st.sidebar.title("🏢 Job Profiles")

# Default Job Descriptions
default_jobs = {
    "Junior Python Developer": """We are looking for a Junior Python Developer. 
    Skills: Python, Streamlit, Pandas, NumPy, SQL. 
    Experience: 0-2 years. 
    Bonus: Internship experience and good communication skills.""",
    
    "Data Scientist": """Seeking a Data Scientist to analyze large datasets.
    Skills: Python, Machine Learning, TensorFlow, Scikit-learn, Statistics.
    Experience: 2+ years.
    Responsibilities: Build predictive models and visualize data.""",
    
    "Full Stack Engineer": """Required: React, Node.js, MongoDB (MERN Stack).
    Experience: Building scalable web applications.
    Skills: REST APIs, Docker, AWS."""
}

# Initialize Session State for Custom Jobs
if 'job_profiles' not in st.session_state:
    st.session_state.job_profiles = default_jobs

# Dropdown to Select Role
selected_role = st.sidebar.selectbox("Select Active Role:", list(st.session_state.job_profiles.keys()) + ["➕ Add New Role"])

# Logic for "Add New Role"
if selected_role == "➕ Add New Role":
    new_role_name = st.sidebar.text_input("Role Name (e.g., HR Manager)")
    new_role_desc = st.sidebar.text_area("Paste Job Description")
    if st.sidebar.button("Save Profile"):
        if new_role_name and new_role_desc:
            st.session_state.job_profiles[new_role_name] = new_role_desc
            st.rerun() # Refresh to show new role
    jd = "" # Empty initially
else:
    # Get the JD from the selected profile
    jd = st.session_state.job_profiles[selected_role]

# --- MAIN PAGE UI ---
st.title("🚀 Smart ATS: Resume Screening & Ranking")
st.markdown(f"### Screening for: **{selected_role if selected_role != '➕ Add New Role' else 'New Role'}**")

# Display Editable JD
jd_input = st.text_area("Job Description (Editable):", value=jd, height=150)

# File Uploader
uploaded_files = st.file_uploader("Upload Resumes (PDF)", type="pdf", accept_multiple_files=True)

submit = st.button("Start Screening")

# 4. PROMPT ENGINEERING
input_prompt = """
Hey Act Like a skilled or very experience ATS (Application Tracking System)
with a deep understanding of tech field, software engineering, data science, data analyst
and big data engineer. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide 
best assistance for improving the resumes. Assign the percentage Matching based 
on Jd and
the missing keywords with high accuracy
resume: {text}
description: {jd}

I want the response in one single string having the structure
{{"JD Match": "%", "MissingKeywords": [], "Profile Summary": ""}}
"""

# 5. EXECUTION LOGIC
if submit:
    if uploaded_files:
        st.write("🔍 Analyzing Resumes...")
        
        ranking_data = []
        progress_bar = st.progress(0)
        
        for index, file in enumerate(uploaded_files):
            try:
                text = input_pdf_text(file)
                final_prompt = input_prompt.format(text=text, jd=jd_input)
                
                # Call AI
                response = get_gemini_response(final_prompt)
                
                # Parse JSON safely
                clean_response = response.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_response)
                
                score = int(data.get("JD Match", "0").replace("%", ""))
                
                ranking_data.append({
                    "Name": file.name,
                    "Score": score,
                    "Missing Keywords": data.get("MissingKeywords", []),
                    "Summary": data.get("Profile Summary", "")
                })
                
                progress_bar.progress((index + 1) / len(uploaded_files))
                
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")
        
        # Sort Leaderboard
        ranking_data.sort(key=lambda x: x["Score"], reverse=True)
        
        # --- DISPLAY RESULTS ---
        st.success("✅ Screening Complete!")
        
        # 1. The Leaderboard Table
        st.subheader("📊 Candidate Rankings")
        st.dataframe(ranking_data, column_order=("Name", "Score", "Missing Keywords"))
        
        # 2. Detailed Winner Card (Professional UI)
        if ranking_data:
            winner = ranking_data[0]
            st.markdown("---")
            st.subheader("🏆 Top Recommendation")
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.metric("Match Score", f"{winner['Score']}%", "Highest")
                with c2:
                    st.markdown(f"### {winner['Name']}")
                    st.info(f"**Summary:** {winner['Summary']}")
                
                if winner['Missing Keywords']:
                    st.write("**⚠️ Missing Skills:**")
                    st.markdown(" ".join([f"`{k}`" for k in winner['Missing Keywords']]))

    else:
        st.warning("Please upload resumes to start.")