import streamlit as st
import spacy

# Cache is important to keep the application fast, with no need to load the model each time.
@st.cache_resource
# This fuction run the model.
def load_model():
    return spacy.load("pt_core_news_lg")

nlp = load_model()

# Front-end code
st.title("Vitae-I: Intelligent Curriculum Analyser")
st.subheader("Phase 1.0: MVP - Entity Extraction")

#place where the user can put the resume
cv_text = st.text_area("Paste the resume text here:", height=300, placeholder="Example: João Silva, Developer at Google")

#Waits for a button click
if st.button("Analyse Resume"):
    if cv_text.strip() == "":
        st.warning("Please paste some text first!")
    else:
        doc = nlp(cv_text)
        
        st.write("### Analysis Results")

        st.write("** Entites found by SpaCy:**")

        entities = [(ent.text, ent.label_) for ent in doc.ents]

        if entities:
            for ent_text, ent_label in entities:
                st.info(f"**{ent_text}** - {ent_label}")
        else:
            st.write("No specific entities found. Try a more detailed text")      