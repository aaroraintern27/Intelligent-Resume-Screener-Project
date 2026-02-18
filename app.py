import streamlit as st
from resume_parser import extract_text_from_pdf_bytes_parallel
from ai_service import compose_prompt, get_gemini_response, format_response_to_text
from config import MAX_RESUMES
import streamlit.components.v1 as components
import hashlib  

def get_files_signature(files):
    file_hashes = []
    for f in files:
        content = f.getvalue()
        content_hash = hashlib.md5(content).hexdigest()
        file_hashes.append(f"{f.name}-{f.size}-{content_hash}")
    return "|".join(sorted(file_hashes))


# PAGE CONFIGURATION
st.set_page_config(
    page_title="Intelligent Resume Screener",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Completely remove Streamlit menu
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


# LOAD CSS
def load_css(file_name: str):
    with open(file_name, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")


st.markdown(
    """
    <link rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    """,
    unsafe_allow_html=True
    )


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

if "formatted_text" not in st.session_state:
    st.session_state.formatted_text = None

if "resume_files_map" not in st.session_state:
    st.session_state.resume_files_map = {}

# Smart tracking 
if "last_analyzed_jd" not in st.session_state:
    st.session_state.last_analyzed_jd = None

if "last_analyzed_files_signature" not in st.session_state:
    st.session_state.last_analyzed_files_signature = None


# SHOW TOAST 

if st.session_state.show_delete_toast:
    st.toast("! File deleted", duration=2)
    st.session_state.show_delete_toast = False


# CACHE WRAPPER

@st.cache_data(show_spinner=False)
def cached_parallel_extraction(pdf_bytes_list):
    return extract_text_from_pdf_bytes_parallel(pdf_bytes_list)


# CALLBACKS

def reset_all():
    st.session_state.uploaded_files = []
    
    st.session_state.jd_input = ""
    st.session_state.process_result = None
    st.session_state.last_prompt = None
    # Clear smart tracking
    st.session_state.last_analyzed_jd = None
    st.session_state.last_analyzed_files_signature = None
    st.session_state.raw_model_response = None
    st.session_state.formatted_text = None
    st.session_state.resume_files_map = {}
    st.session_state.uploader_key += 1
    st.cache_data.clear()

# SIDEBAR
 
with st.sidebar:
    st.markdown(
    """
    <div style="font-size:18px; font-weight:600;">
        <i class="bi bi-cloud-upload-fill" style="margin-right:6px;"></i>
        Upload Resume
    </div>
    <div style="font-size:13px; color:#6b7280; margin-bottom:8px;">
        Upload Your PDF files here
    </div>
    """,
    unsafe_allow_html=True
    )
    #st.caption("Upload Your PDF files here")

    new_files = st.file_uploader(
         label="",   # Keep empty to avoid default text
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


    # SUMMARY
    total_files = len(st.session_state.uploaded_files)
    total_size = sum(f.size for f in st.session_state.uploaded_files)

    # DISPLAY FILES
    if st.session_state.uploaded_files:
        st.markdown(
              f"""
              <div style="margin-top:2px;">
                   <div style="font-weight:600; font-size:16px;">
                         Selected Files ({total_files})
                   </div>
              </div>
               """,
               unsafe_allow_html=True
        )

        st.caption(
             f"Size: {total_size / (1024 * 1024):.2f} MB"
        )

        file_to_delete = None

        for file in st.session_state.uploaded_files:
            col1, col2 = st.columns([8, 2])

            with col1:
                st.markdown(
                    f"""
                    <div class="file-left">
                       <i class="bi bi-file-earmark-text-fill file-icon"></i>
                       <div>
                           <div class="file-name" title="{file.name}">
                                {file.name}
                           </div>
                           <div class="file-size">
                                {file.size / 1024:.1f} KB
                           </div>
                       </div>
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

        
        # Warning if too many files
        if total_files > MAX_RESUMES:
            st.warning(f"⚠️ You uploaded {total_files} files. For best results with the current model (openai/gpt-oss-20b), use max {MAX_RESUMES} resumes.")

    else:
        st.info("No files uploaded yet")

    

# UI RENDER FUNCTIONS 

def render_top_header():
    st.markdown(
        """
        <div class="navbar">
            <div class="nav-title">
                ✨ HeartBeat AI Resume Screener
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_brand_header():
    st.markdown(
        """
        <div class="hero-container">
            <div class="ai-pill">✨ Powered by AI Technology</div>
            <h1 class="hero-title">Screen Resume with AI</h1>
            <p class="hero-subtitle">
                This tool helps you automatically analyze and screen resumes using AI.
                Upload multiple resume files and get insights by comparing them against a job description or custom text.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# JD INPUT WITH BUTTON INSIDE CARD
def render_jd_input():
    st.markdown('<div class="jd-wrapper">', unsafe_allow_html=True)

    st.markdown('<div class="jd-inner">', unsafe_allow_html=True)

    jd_text = st.text_area(
        "Job Description or Custom Text",
        placeholder="Please write Job Description or Custom Text here...",
        height=100,
        key="jd_input"
    )

    has_files = len(st.session_state.uploaded_files) > 0
    #has_jd = bool(jd_text.strip())


    is_disabled = not has_files
    
    # Create 3 columns: empty space, Reset, Analyze
    col_spacer, col_buttons = st.columns([3, 2])

    with col_buttons:
        btn1, btn2 = st.columns(2)

    with btn1:
        if has_files:
           reset_clicked = st.button(
              "Reset All",
               use_container_width=True,
               on_click=reset_all,
               key="reset_btn"
           )

    with btn2:
        analyze_clicked = st.button(
            "Analyze Resume",
            type="primary",
            use_container_width=True,
            disabled=is_disabled
        )


    
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    

    return jd_text, analyze_clicked


def render_footer():
    st.markdown(
        """
        <div class="footer">
            © 2026 HeartBeat AI Resume Screener
        </div>
        """,
        unsafe_allow_html=True
    )


# MAIN PAGE
render_top_header()

with st.container():
    
    render_brand_header()
    jd_text, analyze_clicked = render_jd_input()

    #progress_placeholder = st.empty()

    has_files = len(st.session_state.uploaded_files) > 0
    has_jd = bool(st.session_state.jd_input.strip())
   
    is_processed = st.session_state.process_result is not None

    
    if analyze_clicked:
        progress_placeholder = st.empty()

        if not has_files:
            progress_placeholder.error("❌ Please upload at least one resume file.")
        elif not has_jd:
            progress_placeholder.error("❌ Please enter Job Description or custom text.")
        else:
            if len(st.session_state.uploaded_files) > MAX_RESUMES:
                st.warning(
                    f"⚠️ You uploaded {len(st.session_state.uploaded_files)} files. "
                    f"Processing anyway, but quality may be reduced."
                )

            current_signature = get_files_signature(st.session_state.uploaded_files)

            jd_changed = st.session_state.jd_input != st.session_state.last_analyzed_jd
            files_changed = current_signature != st.session_state.last_analyzed_files_signature
            is_processed = st.session_state.process_result is not None

            
            if is_processed and not jd_changed and not files_changed:
                st.rerun()
            

               #st.session_state.process_result = None
               #st.session_state.formatted_text = None

            try:
                progress_placeholder.info("⏳ Parsing the resumes...")
                pdf_bytes_list = [f.getvalue() for f in st.session_state.uploaded_files]

            
                extracted_json = cached_parallel_extraction(pdf_bytes_list)

                resume_files_map = {}
                for idx, file in enumerate(st.session_state.uploaded_files, start=1):
                    resume_id = f"R-{idx:03d}"
                    resume_files_map[resume_id] = file
                st.session_state.resume_files_map = resume_files_map

                progress_placeholder.info("⏳ Generating the response...")

                prompt = compose_prompt(extracted_json, st.session_state.jd_input)
                st.session_state.last_prompt = prompt

                model_response = get_gemini_response(prompt, extracted_json)
                formatted_text = format_response_to_text(model_response)

                st.session_state.process_result = model_response
                st.session_state.raw_model_response = model_response
                st.session_state.formatted_text = formatted_text

                # Save tracking state
                st.session_state.last_analyzed_jd = st.session_state.jd_input
                st.session_state.last_analyzed_files_signature = current_signature

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

    render_footer()   

