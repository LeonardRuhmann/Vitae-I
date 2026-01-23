import streamlit as st
import spacy

# Cache is important to keep the application fast, with no need to load the model each time.
@st.cache_resource
# This fuction run the model.
def load_model():
    nlp = spacy.load("pt_core_news_lg")
    ruler = nlp.add_pipe("entity_ruler", before="ner")

    skills_list = [
            "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "HTML", "CSS",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
            "Streamlit", "SQL", "MySQL", "PostgreSQL", "MongoDB", "Docker", 
            "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub", "Linux",
            "Machine Learning", "Deep Learning", "NLP", "SpaCy", "Scikit-Learn",
            "Pandas", "NumPy", "TensorFlow", "PyTorch"
        ]

    patterns = [{"label": "SKILL", "pattern": [{"LOWER": skill.lower()}]} for skill in skills_list]

    ruler.add_patterns(patterns)

    return nlp

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

        skills_found = []
        other_entities = []

        for ent in doc.ents:
            if ent.label_ == "SKILL":
                if ent.text not in skills_found:
                    skills_found.append(ent.text)
            else:
                other_entities.append(f"{ent.text} ({ent.label_})")

    st.write("### Skills Identified: ")
    if skills_found:
        st.write(", ".join([f"`{skill}`" for skill in skills_found]))
    else:
        st.info("No specific technical skills found from our list")

    with st.expander("See other entities (Raw data)"):
        st.write(other_entities)