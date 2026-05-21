import spacy
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict
import io
import fitz
import re
from pypdf import PdfReader
import docx

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Uses PyMuPDF to extract text with perfect spacing."""
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            # PyMuPDF is much better at preserving spaces
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            for page in pdf_document:
                text += page.get_text("text") + "\n"
                
        elif filename.lower().endswith('.docx'):
            doc = docx.Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            text = file_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        
    # Clean up excessive newlines
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def chunk_resume_by_headers(text: str) -> dict:
    """Reads line-by-line and buckets text based on standard resume headers."""
    sections = {
        "education": "",
        "experience": "",
        "skills_and_other": ""
    }
    
    current_section = "skills_and_other" # Default bucket
    
    # Split by actual newlines to read line-by-line
    lines = text.split('\n')
    
    for line in lines:
        clean_line = line.strip().upper()
        
        # If the line is short (a header) and contains a keyword, switch buckets
        if len(clean_line) < 20:
            if "EDUCATION" in clean_line:
                current_section = "education"
                continue
            elif "EXPERIENCE" in clean_line or "EMPLOYMENT" in clean_line:
                current_section = "experience"
                continue
            elif "PROJECT" in clean_line or "SKILL" in clean_line:
                current_section = "skills_and_other"
                continue
                
        # Append the line to the active bucket, ensuring it ends with a period for spaCy
        if line.strip():
            sections[current_section] += line.strip() + ". "
            
    return sections

def extract_education(text: str) -> list:
    """Extracts sentences that likely contain educational degrees."""
    # Resumes often lack punctuation at the end of lines. 
    # Replace newlines with periods so spaCy correctly segments sentences!
    text_with_punctuation = text.replace('\n', '. ')
    doc = nlp(text_with_punctuation)
    
    education_keywords = {"bachelor", "master", "phd", "b.tech", "m.tech", "b.s.", "b.a.", "degree", "university", "institute","graduate","graduates","college","diploma","secondary","senior secondary","high school","middle school","school","ssc","hsc", "campus", "b.e.", "b.e"}
    
    # Exclude sentences that are clearly certifications or courses
    exclusion_keywords = {"certificate", "certification", "coursera", "udemy", "professional", "bootcamp"}
    
    education_lines = []
    
    for sent in doc.sents:
        lower_sent = sent.text.lower()
        
        # Check dotted abbreviations with custom word boundary regex to avoid false matches
        has_abbrev = any(re.search(rf'(?<![a-z]){re.escape(ab)}(?![a-z])', lower_sent) for ab in ["b.tech", "m.tech", "b.s.", "b.a.", "b.e.", "b.e", "m.s."])
        # Check standard keywords ensuring whole-word boundaries (fixes "board" in "dashboard")
        has_word = any(re.search(rf'\b{re.escape(kw)}\b', lower_sent) for kw in education_keywords)
        # Standalone board check
        has_board = bool(re.search(r'\bboard\b', lower_sent))
        
        if (has_abbrev or has_word or has_board) and not any(kw in lower_sent for kw in exclusion_keywords):
            education_lines.append(sent.text.strip())
            
    return list(set(education_lines))

def extract_experience(text: str, is_chunked: bool = False) -> list:
    """
    Extracts experience. If the text is already chunked from an Experience
    header, it bypasses the keyword filter and grabs the bullet points.
    """
    doc = nlp(text)
    exp_lines = []
    
    if is_chunked:
        for sent in doc.sents:
            # Grab meaningful sentences (ignore short noise/headers)
            if len(sent.text.split()) > 4: 
                exp_lines.append(sent.text.strip())
        return list(set(exp_lines[:4])) 
        
    # Fallback for unchunked text (like the JD)
    for sent in doc.sents:
        lower_sent = sent.text.lower()
        if "experience" in lower_sent or "worked as" in lower_sent or "fresh" in lower_sent:
            exp_lines.append(sent.text.strip())
            
    return list(set(exp_lines[:3]))

print("Loading AI Models... This may take a few seconds.")

# 1. Initialize spaCy and EntityRuler
nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")
patterns = [
    # Core Developer Skills
    {"label": "SKILL", "pattern": [{"LOWER": "react"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "react.js"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "vue.js"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "machine learning"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "ml"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "python"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "fastapi"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "flask"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "django"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "nodejs"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "node.js"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "postgresql"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "mongodb"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "langchain"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "nlp"}]},
    
    # Frontend & Mobile
    {"label": "SKILL", "pattern": [{"LOWER": "next.js"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "typescript"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "flutter"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "html"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "css"}]},
    
    # Backend & DBs
    {"label": "SKILL", "pattern": [{"LOWER": "c++"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "c"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "supabase"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "sqlite"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "java"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "spring boot"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "aws"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "redis"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "kafka"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "docker"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "git"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "ci/cd"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "sql"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "mysql"}]},
    
    # AI & Data
    {"label": "SKILL", "pattern": [{"LOWER": "streamlit"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "hugging face"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "pandas"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "numpy"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "scikit-learn"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "prompt engineering"}]},
    
    # Growth & Analytics
    {"label": "SKILL", "pattern": [{"LOWER": "r"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "powerbi"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "tableau"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "a/b testing"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "funnel analysis"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "growth marketing"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "bi tools"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "analytics"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "onboarding ux"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "acquisition strategy"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "excel"}]},
    {"label": "SKILL", "pattern": [{"LOWER": "dashboard thinking"}]},
]
ruler.add_patterns(patterns)

# 2. Initialize Sentence Transformer
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("AI Models loaded successfully!")

# Embedding Cache to speed up repeated calculations (e.g. during grid search)
_embedding_cache = {}

def get_embeddings(texts: List[str]):
    if not texts:
        return None
    key = tuple(texts)
    if key not in _embedding_cache:
        _embedding_cache[key] = embedder.encode(texts, convert_to_tensor=True)
    return _embedding_cache[key]

# 3. Normalization Dictionary
degree_mapping = {
    "b.tech": "bachelor's degree",
    "b.s.": "bachelor's degree",
    "bsc": "bachelor's degree",
    "m.tech": "master's degree",
    "b.a.": "bachelor's degree",
    "diploma": "diploma degree",
    "graduates": "bachelor's degree",
    "graduate": "bachelor's degree",
    "college": "bachelor's degree",
    "university": "bachelor's degree",
    "institute": "bachelor's degree",
    "campus": "bachelor's degree",
    "b.e.": "bachelor's degree",
    "b.e": "bachelor's degree"
}

def normalize_text(text_list: List[str]) -> List[str]:
    normalized = []
    for item in text_list:
        lower_item = item.lower()
        for abbr, standard in degree_mapping.items():
            # \b fails on punctuation (like the period in b.s.). 
            # We use negative lookarounds to ensure we aren't matching inside another word.
            pattern = rf'(?<![a-z]){re.escape(abbr)}(?![a-z])'
            lower_item = re.sub(pattern, standard, lower_item)
        normalized.append(lower_item)
    return normalized

def extract_skills_with_context(text: str) -> dict:
    """
    Categorizes extracted skills into mastered, learning, or negated
    based on the lexical window preceding the skill.
    """
    doc = nlp(text)
    categorized_skills = {
        "mastered": [],
        "learning": [],
        "negated": []
    }
    
    # Dictionaries for context detection
    negation_tokens = {"no", "not", "without", "zero", "never"}
    learning_tokens = {"learning", "studying", "pursuing", "beginner", "basic", "hoping", "future"}
    
    for ent in doc.ents:
        if ent.label_ == "SKILL":
            # 5-word window to catch phrases like "am currently studying"
            start_index = max(0, ent.start - 5)
            prior_tokens = [token.lower_ for token in doc[start_index:ent.start]]
            
            status = "mastered"
            for token in prior_tokens:
                if token in negation_tokens:
                    status = "negated"
                    break # Negation takes strict priority
                elif token in learning_tokens:
                    status = "learning"
                    break
                    
            categorized_skills[status].append(ent.text)
            
    # Deduplicate lists before returning
    return {k: list(set(v)) for k, v in categorized_skills.items()}


def calculate_composite_score(cand_data: dict, jd_data: dict, weights_dict: dict, thresholds_dict: dict):
    # --- 1. Identify active sections in the JD ---
    jd_skills = jd_data.get("skills", [])
    cand_skills = cand_data.get("skills", {"mastered": [], "learning": [], "negated": []})
    
    active_sections = []
    if jd_skills:
        active_sections.append("skills")
    if jd_data.get("experience"):
        active_sections.append("experience")
    if jd_data.get("education"):
        active_sections.append("education")
        
    if not active_sections:
        return 0.0, {}
        
    # --- 2. Normalize weights of active sections to sum to 100% ---
    active_weight_sum = sum(weights_dict.get(sec, 0) for sec in active_sections)
    if active_weight_sum == 0:
        normalized_weights = {sec: 100.0 / len(active_sections) for sec in active_sections}
    else:
        normalized_weights = {sec: (weights_dict.get(sec, 0) / active_weight_sum) * 100.0 for sec in active_sections}
        
    total_score = 0.0
    section_scores = {}
    
    # --- 3. Evaluate Skills (Tri-State Logic) ---
    skills_score = 0.0
    if "skills" in active_sections:
        jd_vecs = get_embeddings(jd_skills)
        skill_thresh = thresholds_dict.get("skills", 0.82)
        matches = 0.0
        
        # Check Mastered Skills (Full Point)
        if cand_skills["mastered"]:
            mastered_vecs = get_embeddings(cand_skills["mastered"])
            sim_matrix_m = util.cos_sim(jd_vecs, mastered_vecs)
            for i in range(len(jd_skills)):
                if sim_matrix_m[i].max().item() >= skill_thresh:
                    matches += 1.0
                    continue # Move to next JD skill if matched
                    
        # Check Learning Skills (Half Point) - Only if not already mastered
        if cand_skills["learning"]:
            learning_vecs = get_embeddings(cand_skills["learning"])
            sim_matrix_l = util.cos_sim(jd_vecs, learning_vecs)
            for i in range(len(jd_skills)):
                # If we didn't already give it a full point above, check the learning arrays
                if sim_matrix_l[i].max().item() >= skill_thresh:
                    # We only add 0.5 points for skills currently being studied
                    matches += 0.5 
                    
        skills_score = (matches / len(jd_skills)) * 100
        section_scores["skills"] = round(skills_score, 2)
        total_score += skills_score * (normalized_weights.get("skills", 0) / 100.0)

    # --- 4. Evaluate Experience & Education (Standard Logic) ---
    for section in ['experience', 'education']:
        if section not in active_sections:
            continue
            
        cand_items = cand_data.get(section, [])
        jd_items = jd_data.get(section, [])
        
        # SPECIAL CASE: Fresher Logic
        # If the JD is looking for a "fresh" candidate, experience is essentially a free pass.
        # We give 100% for experience instantly.
        if section == 'experience' and jd_items:
            # Enforce word boundaries for "fresh" / "fresher" and exclude "freshness"
            if any(re.search(r'\bfresh(er)?\b(?!\s*ness)', jd.lower()) for jd in jd_items):
                section_scores[section] = 100.0
                total_score += 100.0 * (normalized_weights.get(section, 0) / 100.0)
                continue
        
        if section == 'education':
            cand_items = normalize_text(cand_items)
            jd_items = normalize_text(jd_items)
            
        if not jd_items or not cand_items:
            section_scores[section] = 0.0
            continue
            
        cand_vecs = get_embeddings(cand_items)
        jd_vecs = get_embeddings(jd_items)
        sim_matrix = util.cos_sim(jd_vecs, cand_vecs)
        
        section_thresh = thresholds_dict.get(section, 0.65)
        


        sec_matches = sum(1 for i in range(len(jd_items)) if sim_matrix[i].max().item() >= section_thresh)
                
        sub_score = (sec_matches / len(jd_items)) * 100
        section_scores[section] = round(sub_score, 2)
        total_score += sub_score * (normalized_weights.get(section, 0) / 100.0)
        
    return round(total_score, 2), section_scores