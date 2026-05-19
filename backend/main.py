from pydantic import BaseModel
from typing import List, Dict
#inporintg the functions from the scoring_engine
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import json

from utils.scoring_engine import (
    extract_skills_with_context, 
    calculate_composite_score,
    extract_text_from_file,
    extract_education,
    extract_experience,
    chunk_resume_by_headers
)

app = FastAPI(title="AI Resume Evaluator API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, change "*" to ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"], # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"], # Allows all headers
)


#Pydantic Schemas
class Weights(BaseModel):
    skills: int
    experience: int
    education: int

class Thresholds(BaseModel):
    skills: float = 0.82
    experience: float = 0.45
    education: float = 0.45

class EvaluationRequest(BaseModel):
    raw_resume_text: str
    raw_jd_text: str
    weights: Weights
    thresholds: Thresholds = Thresholds() 

class EvaluationResponse(BaseModel):
    composite_score: float
    section_breakdown: Dict[str, float]
    extracted_jd_skills: List[str]
    candidate_mastered_skills: List[str]
    candidate_learning_skills: List[str]
    red_flags: List[str]  #stores the negated skills

#API Endpoints

@app.get("/")
async def health_check():
    return {"status": "online", "message": "AI Resume Evaluator API is running. Visit /docs to test."}

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_candidate(
    # Accept files natively
    jd_file: UploadFile = File(...),
    resume_file: UploadFile = File(...),
    # Accept weights as a JSON string from the form
    weights: str = Form(...),
    thresholds: str = Form(default='{"skills": 0.82, "experience": 0.45, "education": 0.40}')
):
    try:
        # 1. Parse the incoming Form JSON
        weights_dict = json.loads(weights)
        thresholds_dict = json.loads(thresholds)
        
        # 2. Read File Bytes
        jd_bytes = await jd_file.read()
        resume_bytes = await resume_file.read()
        
        # 3. Convert Bytes to Text
        jd_text = extract_text_from_file(jd_bytes, jd_file.filename)
        resume_text = extract_text_from_file(resume_bytes, resume_file.filename)
        
        # 4. DYNAMIC EXTRACTION (No more hardcoded arrays!)
        parsed_jd = {
            "skills": extract_skills_with_context(jd_text)["mastered"],
            "experience": extract_experience(jd_text),
            "education": extract_education(jd_text)
        }
        
        candidate_sections = chunk_resume_by_headers(resume_text)
        candidate_skills_dict = extract_skills_with_context(resume_text)

        parsed_resume = {
            "skills": candidate_skills_dict, 
            "experience": extract_experience(candidate_sections["experience"], is_chunked=True),
            "education": extract_education(resume_text)
        }

        print("JD Data:", parsed_jd)
        print("Candidate Data:", parsed_resume)
        
        # 5. Calculate Score
        final_score, breakdown = calculate_composite_score(
            parsed_resume, 
            parsed_jd, 
            weights_dict, 
            thresholds_dict
        )
        
        # 6. Generate Flags
        red_flags = [f"Candidate explicitly stated a lack of experience with: {missing}" for missing in candidate_skills_dict["negated"]]
        
        print(f"\n--- FINAL SCORE COMPUTATION ---")
        print(f"Composite Score: {final_score}")
        print(f"Section Breakdown: {breakdown}")
        print(f"-------------------------------\n")
            
        return EvaluationResponse(
            composite_score=final_score,
            section_breakdown=breakdown,
            extracted_jd_skills=parsed_jd["skills"],
            candidate_mastered_skills=candidate_skills_dict["mastered"],
            candidate_learning_skills=candidate_skills_dict["learning"],
            red_flags=red_flags
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))