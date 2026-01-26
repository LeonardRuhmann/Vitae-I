import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/analyze"

# Front-end code
st.title("Vitae-I: Intelligent Curriculum Analyser")

#place where the user can put the resume
# cv_text = st.text_area("Paste the resume text here:", height=300, placeholder="Example: João Silva, Developer at Google")
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
                    entities = data.get("entities", [])

                    organzations = []
                    locations = []
                    people = []

                    for entity in entities:
                        label = entity.get("label")
                        text = entity.get("text")

                        if label == "ORG":
                            organzations.append(text)
                        elif label == "LOC":
                            locations.append(text)
                        elif label == "PER":
                            people.append(text)

                    st.markdown("### Skills Identified (from API)")

                    if skills:
                        skills_text = ", ".join([f"{skill}" for skill in skills])
                        st.markdown(
                            f'<p style="font-size: 1.3em; font-weight: bold; color: white; background-color: #157353; border-radius: 20px; padding: 15px; margin: 10px 0;">{skills_text}</p>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("No skills found.")
                    
                    with st.expander("### Extracted content:"):
                        column1, column2, column3 = st.columns(3)
                        with column1:
                            st.write("#### Organizations")
                            if organzations:
                                for organization in list(set(organzations)):
                                    st.write(f"- {organization}")
                            else:
                                st.caption("No organizations found.")
                            
                        with column2:
                            st.write("#### Locations:")
                            if locations:
                                for location in list(set(locations)):
                                    st.write(f"- {location}")
                            else:
                                st.caption("No locations found.")

                        with column3:
                            st.write("#### People:")
                            if people:
                                for person in list(set(people)):
                                    st.write(f"- {person}")
                            else:
                                st.caption("No people found.")
                        with st.expander("see extracted text"):
                            st.text(data.get("text_preview",  "No preview avaliable"))

                else:
                    st.error(f"API ERROR: {response.status_code}")
            
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the Brain! Is the API server running?"
                )