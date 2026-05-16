# AI Resume Evaluator (Phase 1)

An automated, AI-powered recruitment pipeline designed to ingest unstructured resumes, extract key data points using Natural Language Processing (NLP), and evaluate candidates against a dynamically weighted job description (JD). 

This system mitigates recruiter fatigue by automatically pausing intake once a dynamic threshold of top-tier candidates is reached, presenting the ranked results securely on a modern web dashboard.

## 🚀 Key Features

* **Event-Driven Data Ingestion:** Automatically fetches and processes incoming applications sent to a designated email inbox via Azure Logic Apps.
* **Domain-Specific NLP Parsing:** Utilizes a custom Transformer-based Named Entity Recognition (NER) model to convert unstructured PDFs/Docs into structured JSON profiles (Skills, Experience, Education).
* **Semantic Scoring Engine:** Employs vector embeddings and cosine similarity to evaluate candidates against hiring manager-defined criteria, resolving the "brittle keyword" problem (e.g., matching "ML" with "Machine Learning").
* **Dynamic Auto-Pause System:** Operates as a fail-safe state machine, automatically halting ingestion and alerting managers when a target volume of high-scoring candidates is achieved.
* **Secure API Architecture:** Endpoints are protected via OAuth2 / JWT authentication, ensuring only authorized webhooks and users can access the pipeline.

## 🛠️ Technology Stack

**Frontend:**
* React.js (Single Page Application)
* Tailwind CSS (Styling)

**Backend & Architecture:**
* Python (FastAPI)
* MongoDB (NoSQL Document Storage)
* Azure Logic Apps (Webhook & Email Integration)
* OAuth2 with JWT (Authentication)

**Machine Learning & AI:**
* HuggingFace Transformers / spaCy (NER Pipeline)
* `all-MiniLM-L6-v2` (Vector Embeddings)
* Scikit-Learn (Evaluation metrics and Grid Search tuning)

## 🏗️ System Architecture & Data Flow

1.  **JD Configuration:** The hiring manager sets percentage weights for specific job requirements via the React UI. Data is serialized to MongoDB.
2.  **Automated Intake:** Candidate emails resume -> Azure Logic App triggers -> Authenticates via JWT -> POSTs document to FastAPI backend.
3.  **Extraction (ETL):** FastAPI strips text (and applies OCR if necessary). The NER model extracts entities into a JSON object. The raw PDF is saved locally, and the JSON is stored in MongoDB.
4.  **Evaluation:** The semantic engine vectorizes both the candidate's skills and the JD. It calculates cosine similarity, applies the manager's weights, and generates a **0–100% Composite Fit Score**.
5.  **Threshold Control:** The system checks the auto-pause threshold. If "critical mass" is reached, ingestion halts and alerts are dispatched.
6.  **Review Dashboard:** Managers access the React UI to view a comparative table of ranked candidates with transparent scoring breakdowns.

## 📊 Model Evaluation & Tuning

To ensure absolute reliability in the parsing and scoring mechanics, this repository includes offline evaluation metrics. 

See the `model_evaluation.ipynb` notebook in the root directory for:
* **F1-Score and Recall metrics** for the Transformer NER model.
* **Grid Search Hyperparameter Tuning (HPT)** used to define the optimal cosine similarity threshold for the semantic scoring engine.

## 💻 Local Setup & Installation

### Prerequisites
* Python 3.10+
* Node.js & npm
* MongoDB (Local instance or Atlas URI)

### Backend Setup
```bash
# Clone the repository
git clone [https://github.com/aniketh2207/ai-resume-evaluator.git](https://github.com/aniketh2207/ai-resume-evaluator.git)
cd ai-resume-evaluator/backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env to include your MongoDB URI and JWT Secret

# Run the FastAPI server
uvicorn main:app --reload
