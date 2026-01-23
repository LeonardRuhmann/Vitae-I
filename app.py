import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/analyze"

# Front-end code
st.title("Vitae-I: Intelligent Curriculum Analyser")

#place where the user can put the resume
cv_text = st.text_area("Paste the resume text here:", height=300, placeholder="Example: João Silva, Developer at Google")

#Waits for a button click
if st.button("Analyse Resume"):
    if cv_text.strip() == "":
        st.warning("Please paste some text first!")
    else:
        # doc = nlp(cv_text)
        try:
            with st.spinner("consulting the AI brain..."):
                response = requests.post(API_URL, json={"text": cv_text})
                
            if response.status_code == 200:
                data = response.json()

                skills = data.get("skills", [])
                entities = data.get("entities", [])

                st.write("### Skills Identified (from API)")

                if skills:
                    st.write(", ".join([f"`{skill}`" for skill in skills]))
                else:
                    st.info("No skills found.")
                
                with st.expander("See raw entities"):
                    st.json(entities)
            else:
                st.error(f"API ERROR: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the Brain! Is the API server running?"
            )