import os
import requests
import streamlit as st

API_URL = os.environ.get("VITAE_API_URL", "http://127.0.0.1:8000/analyze")


def load_css(filepath: str):
    """Injects a CSS file into the Streamlit app."""
    with open(filepath) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Front-end code
load_css("styles/styles.css")
st.title("Vitae-I: Intelligent Curriculum Analyser")

#place where the user can put the resume
uploaded_file = st.file_uploader("Upload your resume (PDF only", type=["pdf"])
if uploaded_file is not None:
    st.success("File uploaded sucessfully!")

    #Waits for a button click
    if st.button("Analyse Resume"):
        with st.spinner("Reading PDF and Extracting Intelligence..."):
            try:
                # prepare the file for the API
                # we send the bytes directly to the backend
                files = {"file": ("resume.pdf", uploaded_file.getvalue(), "application/pdf")}

                response = requests.post(API_URL, files=files)

                if response.status_code == 200:
                    data = response.json()

                    skills = data.get("skills", [])
                    people = data.get("people", [])
                    info = data.get("info", [])

                    st.markdown("### Skills Identified (from API)")

                    if skills:
                        skills_text = ", ".join([f"{skill}" for skill in skills])
                        st.markdown(
                            f'<p class="skills-tag">{skills_text}</p>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("No skills found.")
                    
                    with st.expander("### Extracted content:"):
                        column1, column2 = st.columns([1, 3])
                        
                        with column1:
                            st.write("#### Candidate")
                            if people:
                                for person in list(set(people)):
                                    st.write(f"- {person}")
                            else:
                                st.caption("No people found.")
                        
                        with column2:
                            st.write("#### Key Entities")
                            if info:
                                # Display as comma-separated tags
                                info_text = ", ".join([f"{item}" for item in info])
                                st.markdown(
                                    f'<p class="info-tag">{info_text}</p>',
                                    unsafe_allow_html=True
                                )
                            else:
                                st.caption("No key entities found.")
                        
                        with st.expander("see extracted text"):
                            st.text(data.get("text_preview",  "No preview avaliable"))

                else:
                    st.error(f"API ERROR: {response.status_code}")
            
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the Brain! Is the API server running?"
                )