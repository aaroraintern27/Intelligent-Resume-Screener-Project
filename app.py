import streamlit as st
from resume_parser import extract_text_from_pdf_bytes_parallel
from ai_service import compose_prompt, get_gemini_response, format_response_to_text
from config import MAX_RESUMES
import streamlit.components.v1 as components

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Intelligent Resume Screener",
    layout="wide"
)

# LOAD CSS
def load_css(file_name: str):
    with open(file_name, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")


# SESSION STATE

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "show_delete_toast" not in st.session_state:
    st.session_state.show_delete_toast = False
   
if "process_result" not in st.session_state:
    st.session_state.process_result = None

if "jd_input" not in st.session_state:
    st.session_state.jd_input = ""

if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None

if "raw_model_response" not in st.session_state:
    st.session_state.raw_model_response = None

if "formatted_text" not in st.session_state:
    st.session_state.formatted_text = None

if "resume_files_map" not in st.session_state:
    st.session_state.resume_files_map = {}  # Maps R-001 -> original file




# SHOW TOAST

if st.session_state.show_delete_toast:
    st.toast("! File deleted", duration=2)
    st.session_state.show_delete_toast = False


# CACHE WRAPPER

@st.cache_data(show_spinner=False)
def cached_parallel_extraction(pdf_bytes_list):
    return extract_text_from_pdf_bytes_parallel(pdf_bytes_list)



# CALLBACKS 

def clear_chat_and_jd():
    st.session_state.chat_history = []
    st.session_state.jd_input = ""
    st.session_state.process_result = None
    st.session_state.last_prompt = None
    st.session_state.raw_model_response = None
    st.session_state.formatted_text = None

def reset_all():
    st.session_state.uploaded_files = []
    st.session_state.chat_history = []
    st.session_state.jd_input = ""
    st.session_state.process_result = None
    st.session_state.last_prompt = None
    st.session_state.raw_model_response = None
    st.session_state.formatted_text = None
    st.session_state.resume_files_map = {}
    st.session_state.uploader_key += 1
    st.cache_data.clear()



# UI RENDER FUNCTIONS

def render_brand_header():
    st.markdown(
        """
        <div class="brand-header">
            <div class="brand-logo">📄</div>
            <h1 class="brand-title">Intelligent Resume Screener</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_info_section():
    st.markdown(
        """
        <div class="info-container">
            <div class="info-text">
                This tool helps you automatically analyze and screen resumes using AI.
                Upload multiple resume files and get insights by comparing them against a
                job description or custom text.
            </div>
            <ul class="info-list">
                <li>Upload multiple resume files using the sidebar.</li>
                <li>Enter a Job Description or Custom Text below.</li>
                <li>Click "Final Submit" to analyze and rank candidates intelligently.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_jd_input():
    st.markdown('<div class="jd-container">', unsafe_allow_html=True)

    jd_text = st.text_area(
        label="Job Description Or Custom Text",
        placeholder="Enter Job Description or custom-text here…",
        height=10,
        key="jd_input"
    )

    st.markdown('</div>', unsafe_allow_html=True)
    return jd_text


# MAIN PAGE
with st.container():
    render_brand_header()
    render_info_section()
    jd_text = render_jd_input()

    # Progress messages placeholder (right below text area)
    progress_placeholder = st.empty()

    # Check if we have files and JD
    has_files = len(st.session_state.uploaded_files) > 0
    has_jd = bool(st.session_state.jd_input.strip())
    
    # Check if already processed
    is_processed = st.session_state.process_result is not None

    st.markdown('<div class="final-btn-row">', unsafe_allow_html=True)

    # Always enable button - check requirements when clicked
    if st.button("Final Submit"):
        # Validation: Check if requirements are met
        if not has_files:
            progress_placeholder.error("❌ Please upload at least one resume file.")
        elif not has_jd:
            progress_placeholder.error("❌ Please enter Job Description or custom text.")
        elif is_processed:
            progress_placeholder.info("ℹ️ Results already generated. Click 'Clear Chat' to analyze new resumes.")
        else:
            # All requirements met - proceed with processing
            # Show warning if too many files (but continue processing)
            if len(st.session_state.uploaded_files) > MAX_RESUMES:
                st.warning(f"⚠️ You uploaded {len(st.session_state.uploaded_files)} files. The current model (openai/gpt-oss-20b with 8k context) works best with max {MAX_RESUMES} resumes. Processing anyway, but quality may be reduced.")
            
            # Step 1: Parse resumes
            progress_placeholder.info("⏳ Parsing the resumes...")
            pdf_bytes_list = [f.getvalue() for f in st.session_state.uploaded_files]
            
            try:
                extracted_json = cached_parallel_extraction(pdf_bytes_list)
                
                # Create mapping of resume IDs to original files for download
                resume_files_map = {}
                for idx, file in enumerate(st.session_state.uploaded_files, start=1):
                    resume_id = f"R-{idx:03d}"
                    resume_files_map[resume_id] = file
                st.session_state.resume_files_map = resume_files_map
                
                # Step 2: Generate response
                progress_placeholder.info("⏳ Generating the response...")
                
                # Compose prompt for AI using parsed resumes and JD input
                # Use session_state value which has the typed text
                prompt = compose_prompt(extracted_json, st.session_state.jd_input)
                
                # Save prompt for debugging / replay
                st.session_state.last_prompt = prompt
                
                # Call AI model and get structured JSON response
                model_response = get_gemini_response(prompt, extracted_json)
                
                # Convert JSON to human-readable text
                formatted_text = format_response_to_text(model_response)
                
                # Store both JSON and formatted text for UI display
                st.session_state.process_result = model_response
                st.session_state.raw_model_response = model_response
                st.session_state.formatted_text = formatted_text
                
                progress_placeholder.success("✅ Response generated successfully!")
                st.rerun()
                
            except Exception as e:
                progress_placeholder.error(f"❌ Error: {str(e)}")
                st.error(f"Error processing resumes: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Display results if available
    if st.session_state.process_result:
        st.markdown("---")
        st.subheader("📊 Analysis Result")
        
        # Show formatted text
        if st.session_state.formatted_text:
            st.text(st.session_state.formatted_text)
        
        # Add download section for suitable candidates
        if st.session_state.process_result.get("candidates"):
            st.markdown("---")
            st.subheader("📥 Download Suitable Candidate Resumes")
            
            suitable_candidates = [
                c for c in st.session_state.process_result["candidates"]
                if c.get("is_suitable", False)
            ]
            
            if suitable_candidates:
                st.write(f"Found {len(suitable_candidates)} suitable candidate(s)")
                
                # Create columns for download buttons
                cols = st.columns(min(len(suitable_candidates), 3))
                
                for idx, candidate in enumerate(suitable_candidates):
                    candidate_id = candidate.get("id")  # R-001 (internal use only)
                    candidate_name = candidate.get("name", "Unknown Candidate")
                    score = candidate.get("score_percentage", 0)
                    
                    col_idx = idx % 3
                    with cols[col_idx]:
                        # Get the original file for this candidate using internal ID
                        if candidate_id in st.session_state.resume_files_map:
                            original_file = st.session_state.resume_files_map[candidate_id]
                            
                            # Download button shows name and score (no R-001 ID)
                            st.download_button(
                                label=f"📄 {candidate_name}\nMatch: {score}%",
                                data=original_file.getvalue(),
                                file_name=original_file.name,  # Keep original filename
                                mime="application/pdf",
                                key=f"download_{candidate_id}",
                                use_container_width=True
                            )
            else:
                st.info("No suitable candidates found (score >= 70%)")


# SIDEBAR
with st.sidebar:
    st.header("📂 Document Management")
    st.caption("Upload resume files to analyze")

    new_files = st.file_uploader(
        "Drag and drop files here",
        type=["pdf"],
        accept_multiple_files=True,
        key=st.session_state.uploader_key
    )

    # ADD FILES
    if new_files:
        existing_names = {f.name for f in st.session_state.uploaded_files}
        for f in new_files:
            if f.name not in existing_names:
                st.session_state.uploaded_files.append(f)

    # DISPLAY FILES
    if st.session_state.uploaded_files:
        st.markdown("### 📄 Selected Files")

        file_to_delete = None

        for file in st.session_state.uploaded_files:
            col1, col2 = st.columns([8, 2])

            with col1:
                st.markdown(
                    f"""
                    <div class="file-name" title="{file.name}">
                        {file.name}
                    </div>
                    <div class="file-size">
                        {file.size / 1024:.1f} KB
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                if st.button("🗑", key=f"delete_{file.name}", use_container_width=True):
                    file_to_delete = file.name

        # DELETE FILE (WITH RERUN)
        if file_to_delete:
            st.session_state.uploaded_files = [
                f for f in st.session_state.uploaded_files
                if f.name != file_to_delete
            ]

            st.session_state.process_result = None
            st.session_state.formatted_text = None
            st.session_state.resume_files_map = {}
            st.session_state.uploader_key += 1
            st.session_state.show_delete_toast = True
            st.rerun()

        # SUMMARY
        total_files = len(st.session_state.uploaded_files)
        total_size = sum(f.size for f in st.session_state.uploaded_files)

        st.divider()
        st.write(f"**Total:** {total_files} files")
        st.write(f"**Size:** {total_size / (1024 * 1024):.2f} MB")
        
        # Warning if too many files
        if total_files > MAX_RESUMES:
            st.warning(f"⚠️ You uploaded {total_files} files. For best results with the current model (openai/gpt-oss-20b), use max {MAX_RESUMES} resumes.")

    else:
        st.info("No files uploaded yet")

    # CONTROLS
    st.divider()
    st.markdown("Controls")

    col1, col2 = st.columns(2)

    with col1:
        st.button(
            "Clear Chat",
            use_container_width=True,
            on_click=clear_chat_and_jd
        )

    with col2:
        st.button(
            "🔄 Reset All",
            use_container_width=True,
            on_click=reset_all
        )

