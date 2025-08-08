import streamlit as st
import requests
import json
import time
from datetime import datetime
import pandas as pd
from typing import Dict, Any, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="Resume Parser",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend configuration
BACKEND_URL = "http://127.0.0.1:8000"
API_BASE = f"{BACKEND_URL}/api/v1"

class ResumeParserUI:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.api_base = API_BASE
    
    def check_backend_health(self) -> bool:
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def parse_resume_sync(self, file, use_llm_fallback: bool = True, llm_provider: str = "openai") -> Dict[str, Any]:
        """Parse resume synchronously"""
        try:
            files = {"file": (file.name, file.getvalue(), file.type)}
            data = {
                "use_llm_fallback": use_llm_fallback,
                "llm_provider": llm_provider
            }
            
            with st.spinner("Processing resume..."):
                response = requests.post(
                    f"{self.api_base}/parse",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def parse_resume_async(self, file, use_llm_fallback: bool = True, llm_provider: str = "openai") -> Dict[str, Any]:
        """Parse resume asynchronously"""
        try:
            files = {"file": (file.name, file.getvalue(), file.type)}
            data = {
                "use_llm_fallback": use_llm_fallback,
                "llm_provider": llm_provider
            }
            
            # Submit job
            response = requests.post(
                f"{self.api_base}/parse/async",
                files=files,
                data=data,
                timeout=10
            )
            
            result = response.json()
            if result.get("success") and result.get("job_id"):
                return self.poll_job_status(result["job_id"])
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def poll_job_status(self, job_id: str) -> Dict[str, Any]:
        """Poll job status until completion"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        max_attempts = 60  # 60 seconds max
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.api_base}/job/{job_id}", timeout=5)
                job_status = response.json()
                
                status = job_status.get("status", "unknown")
                progress = min((attempt + 1) / max_attempts, 0.9)
                
                if status == "pending":
                    status_text.text("⏳ Job queued, waiting to process...")
                    progress_bar.progress(0.1)
                elif status == "processing":
                    status_text.text("🔄 Processing resume...")
                    progress_bar.progress(0.5)
                elif status == "completed":
                    status_text.text("✅ Processing completed!")
                    progress_bar.progress(1.0)
                    time.sleep(0.5)  # Brief pause to show completion
                    progress_bar.empty()
                    status_text.empty()
                    return {"success": True, "data": job_status.get("result")}
                elif status == "failed":
                    progress_bar.empty()
                    status_text.empty()
                    return {"success": False, "error": job_status.get("error", "Unknown error")}
                
                time.sleep(1)
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                return {"success": False, "error": f"Status check failed: {str(e)}"}
        
        progress_bar.empty()
        status_text.empty()
        return {"success": False, "error": "Job timeout after 60 seconds"}

def display_personal_info(personal_info: Dict[str, Any]):
    """Display personal information section"""
    st.subheader("👤 Personal Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if personal_info.get("full_name"):
            st.write(f"**Name:** {personal_info['full_name']}")
        if personal_info.get("email"):
            st.write(f"**Email:** {personal_info['email']}")
        if personal_info.get("phone"):
            st.write(f"**Phone:** {personal_info['phone']}")
    
    with col2:
        if personal_info.get("linkedin"):
            st.write(f"**LinkedIn:** [{personal_info['linkedin']}]({personal_info['linkedin']})")
        if personal_info.get("github"):
            st.write(f"**GitHub:** [{personal_info['github']}]({personal_info['github']})")
        if personal_info.get("portfolio"):
            st.write(f"**Portfolio:** [{personal_info['portfolio']}]({personal_info['portfolio']})")

def display_experience(experience: list):
    """Display experience section"""
    st.subheader("💼 Work Experience")
    
    if not experience:
        st.info("No work experience found")
        return
    
    for i, exp in enumerate(experience):
        with st.expander(f"{exp.get('position', 'Unknown Position')} - {exp.get('company', 'Unknown Company')}", expanded=i == 0):
            col1, col2 = st.columns(2)
            
            with col1:
                if exp.get("position"):
                    st.write(f"**Position:** {exp['position']}")
                if exp.get("company"):
                    st.write(f"**Company:** {exp['company']}")
            
            with col2:
                if exp.get("start_date"):
                    end_date = exp.get('end_date', 'Present' if exp.get('is_current') else 'Unknown')
                    st.write(f"**Duration:** {exp['start_date']} - {end_date}")
            
            if exp.get("description"):
                st.write("**Description:**")
                st.write(exp['description'])
            
            if exp.get("achievements"):
                st.write("**Key Achievements:**")
                for achievement in exp['achievements']:
                    st.write(f"• {achievement}")

def display_education(education: list):
    """Display education section"""
    st.subheader("🎓 Education")
    
    if not education:
        st.info("No education information found")
        return
    
    for edu in education:
        with st.expander(f"{edu.get('degree', 'Degree')} - {edu.get('institution', 'Institution')}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if edu.get("degree"):
                    st.write(f"**Degree:** {edu['degree']}")
                if edu.get("field_of_study"):
                    st.write(f"**Field:** {edu['field_of_study']}")
            
            with col2:
                if edu.get("institution"):
                    st.write(f"**Institution:** {edu['institution']}")
                if edu.get("graduation_date"):
                    st.write(f"**Graduation:** {edu['graduation_date']}")
                if edu.get("gpa"):
                    st.write(f"**GPA:** {edu['gpa']}")

def display_skills(skills: list):
    """Display skills section"""
    st.subheader("🛠️ Skills")
    
    if not skills:
        st.info("No skills found")
        return
    
    for skill_group in skills:
        category = skill_group.get("category", "Skills")
        skill_list = skill_group.get("skills", [])
        
        if skill_list:
            st.write(f"**{category}:**")
            # Display skills as tags
            skills_text = " • ".join(skill_list)
            st.write(skills_text)
            st.write("")

def display_projects(projects: list):
    """Display projects section"""
    st.subheader("🚀 Projects")
    
    if not projects:
        st.info("No projects found")
        return
    
    for project in projects:
        with st.expander(f"{project.get('name', 'Unnamed Project')}", expanded=False):
            if project.get("description"):
                st.write("**Description:**")
                st.write(project['description'])
            
            if project.get("technologies"):
                st.write("**Technologies:**")
                tech_text = " • ".join(project['technologies'])
                st.write(tech_text)
            
            col1, col2 = st.columns(2)
            with col1:
                if project.get("url"):
                    st.write(f"**URL:** [{project['url']}]({project['url']})")
            with col2:
                if project.get("start_date"):
                    end_date = project.get('end_date', 'Ongoing')
                    st.write(f"**Duration:** {project['start_date']} - {end_date}")

def display_certifications(certifications: list):
    """Display certifications section"""
    st.subheader("📜 Certifications")
    
    if not certifications:
        st.info("No certifications found")
        return
    
    for cert in certifications:
        with st.expander(f"{cert.get('name', 'Certification')}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if cert.get("issuer"):
                    st.write(f"**Issuer:** {cert['issuer']}")
                if cert.get("date"):
                    st.write(f"**Date:** {cert['date']}")
            
            with col2:
                if cert.get("credential_id"):
                    st.write(f"**Credential ID:** {cert['credential_id']}")

def display_languages(languages: list):
    """Display languages section"""
    st.subheader("🌐 Languages")
    
    if not languages:
        st.info("No languages found")
        return
    
    for lang in languages:
        lang_name = lang.get("language", "Unknown")
        proficiency = lang.get("proficiency", "")
        if proficiency:
            st.write(f"• **{lang_name}**: {proficiency}")
        else:
            st.write(f"• {lang_name}")

def display_metadata(data: Dict[str, Any]):
    """Display parsing metadata"""
    st.subheader("📊 Parsing Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        confidence = data.get("confidence_score", 0)
        st.metric("Confidence Score", f"{confidence:.2%}")
    
    with col2:
        method = data.get("parsing_method", "unknown")
        method_display = {
            "rule_based": "Rule-Based",
            "llm_openai": "OpenAI GPT",
            "llm_anthropic": "Claude"
        }.get(method, method.title())
        st.metric("Parsing Method", method_display)
    
    with col3:
        processing_time = data.get("processing_time", 0)
        st.metric("Processing Time", f"{processing_time:.2f}s")

def display_json_data(data: Dict[str, Any]):
    """Display raw JSON data"""
    with st.expander("🔍 Raw JSON Data", expanded=False):
        st.json(data)

def main():
    # Title and header
    st.title("📄 Resume Parser")
    st.markdown("Upload your resume and get structured data extraction with AI-powered parsing")
    
    # Initialize UI
    parser_ui = ResumeParserUI()
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Check backend health
    if not parser_ui.check_backend_health():
        st.error("❌ Backend server is not reachable. Please ensure the server is running at http://127.0.0.1:8000")
        st.stop()
    else:
        st.sidebar.success("✅ Backend connected")
    
    # Processing options
    st.sidebar.subheader("Processing Options")
    processing_mode = st.sidebar.radio(
        "Processing Mode",
        ["Synchronous", "Asynchronous"],
        help="Synchronous: Wait for result. Asynchronous: Submit job and poll status."
    )
    
    use_llm_fallback = st.sidebar.checkbox(
        "Use LLM Fallback",
        value=True,
        help="Use AI models when rule-based parsing confidence is low"
    )
    
    llm_provider = st.sidebar.selectbox(
        "LLM Provider",
        ["openai", "anthropic"],
        help="Choose AI provider for fallback parsing"
    )
    
    # File upload
    st.header("📤 Upload Resume")
    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=['pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg'],
        help="Supported formats: PDF, DOCX, DOC, TXT, PNG, JPG, JPEG"
    )
    
    if uploaded_file is not None:
        # File information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Filename:** {uploaded_file.name}")
        with col2:
            st.info(f"**Size:** {uploaded_file.size:,} bytes")
        with col3:
            st.info(f"**Type:** {uploaded_file.type}")
        
        # Parse button
        if st.button("🚀 Parse Resume", type="primary"):
            start_time = time.time()
            
            # Choose processing mode
            if processing_mode == "Synchronous":
                result = parser_ui.parse_resume_sync(
                    uploaded_file, use_llm_fallback, llm_provider
                )
            else:
                result = parser_ui.parse_resume_async(
                    uploaded_file, use_llm_fallback, llm_provider
                )
            
            total_time = time.time() - start_time
            
            # Display results
            if result.get("success"):
                data = result.get("data", {})
                
                st.success(f"✅ Resume parsed successfully in {total_time:.2f}s")
                
                # Display parsed sections
                if data.get("personal_info"):
                    display_personal_info(data["personal_info"])
                
                if data.get("summary"):
                    st.subheader("📋 Summary")
                    st.write(data["summary"])
                
                if data.get("experience"):
                    display_experience(data["experience"])
                
                if data.get("education"):
                    display_education(data["education"])
                
                if data.get("skills"):
                    display_skills(data["skills"])
                
                if data.get("projects"):
                    display_projects(data["projects"])
                
                if data.get("certifications"):
                    display_certifications(data["certifications"])
                
                if data.get("languages"):
                    display_languages(data["languages"])
                
                # Metadata
                display_metadata(data)
                
                # Raw JSON
                display_json_data(data)
                
                # Download option
                st.header("💾 Export Results")
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"parsed_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
            else:
                error_msg = result.get("error", "Unknown error occurred")
                st.error(f"❌ Parsing failed: {error_msg}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>Resume Parser • Built with Streamlit & FastAPI</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()