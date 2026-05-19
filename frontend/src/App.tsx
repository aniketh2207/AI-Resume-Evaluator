import React, { useState } from 'react';
import './App.css'; // Make sure to import the CSS

export default function Dashboard() {
  // 1. Form State
  const [jdFile, setJdFile] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [weights, setWeights] = useState({
    skills: 50,
    experience: 30,
    education: 20
  });

  // 2. Output State
  // useState returns 2 things, current state value and function to update the state value
  const [results, setResults] = useState(null); 
  const [loading, setLoading] = useState(false); // this is a state variable that is used to store the loading state
  const [error, setError] = useState(null);

  // 3. Handle Weight Changes safely
  const handleWeightChange = (e) => {
    const { name, value } = e.target;
    setWeights(prev => ({
      ...prev,
      [name]: parseInt(value) || 0
    }));
  };

  // 4. API Submission
  const handleEvaluate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const formData = new FormData();
    if (jdFile) formData.append('jd_file', jdFile);
    if (resumeFile) formData.append('resume_file', resumeFile);
    formData.append('weights', JSON.stringify(weights));
    // We omit thresholds to let the backend use its defaults

    try {
      const response = await fetch('http://localhost:8000/evaluate', {
        method: 'POST',
        // Do not set Content-Type header when using FormData
        body: formData
      });

      if (!response.ok) throw new Error("API failed to process request");
      
      const data = await response.json();
      // cant use normal results = data, instead need to use setResults to update the state variable result
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColorClass = (score) => {
    if (score >= 75) return 'score-excellent';
    if (score >= 50) return 'score-good';
    return 'score-poor';
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>AI Resume Evaluator</h1>
        <p>Smart semantic matching to find the perfect candidate</p>
      </div>
      
      <div className="dashboard-grid">
        
        {/* LEFT COLUMN: Input Form */}
        <div className="glass-panel card">
          <h2>Evaluation Criteria</h2>
          <form onSubmit={handleEvaluate}>
            <div className="form-group">
              <label>Job Description Document</label>
              <input 
                type="file"
                className="form-control"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setJdFile(e.target.files ? e.target.files[0] : null)}
                required
                style={{ padding: '10px', background: 'rgba(255, 255, 255, 0.5)' }}
              />
            </div>

            <div className="form-group">
              <label>Candidate Resume</label>
              <input 
                type="file"
                className="form-control"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setResumeFile(e.target.files ? e.target.files[0] : null)}
                required
                style={{ padding: '10px', background: 'rgba(255, 255, 255, 0.5)' }}
              />
            </div>

            <div className="weights-container">
              <h3>Manager Scoring Weights</h3>
              <div className="weights-grid">
                <div className="weight-input-group">
                  <label>
                    Skills (%)
                    <input className="weight-input" type="number" name="skills" value={weights.skills} onChange={handleWeightChange} max="100" min="0" />
                  </label>
                </div>
                <div className="weight-input-group">
                  <label>
                    Experience (%)
                    <input className="weight-input" type="number" name="experience" value={weights.experience} onChange={handleWeightChange} max="100" min="0" />
                  </label>
                </div>
                <div className="weight-input-group">
                  <label>
                    Education (%)
                    <input className="weight-input" type="number" name="education" value={weights.education} onChange={handleWeightChange} max="100" min="0" />
                  </label>
                </div>
              </div>
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? (
                <>
                  <div className="loading-spinner" style={{ width: '20px', height: '20px', borderWidth: '2px', margin: 0, borderTopColor: 'white' }}></div>
                  Evaluating...
                </>
              ) : 'Run AI Evaluation'}
            </button>
            
            {error && (
              <div className="error-message">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                {error}
              </div>
            )}
          </form>
        </div>

        {/* RIGHT COLUMN: Results Dashboard */}
        <div className="glass-panel card">
          <h2>Evaluation Results</h2>
          
          {!results && !loading && (
            <div className="results-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: '1rem', opacity: 0.5 }}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              <p>Awaiting submission... Enter a Job Description and Resume to see the AI analysis.</p>
            </div>
          )}
          
          {loading && (
            <div className="results-empty">
              <div className="loading-spinner"></div>
              <p>Running semantic matching...</p>
            </div>
          )}

          {results && (
            <div className="results-content">
              <div className="score-display">
                <div className="score-circle">
                  <h1 className={getScoreColorClass(results.composite_score)}>
                    {results.composite_score}
                  </h1>
                </div>
                <p style={{ marginTop: '1rem', color: 'var(--text-muted)', fontWeight: 500 }}>Overall Match Score</p>
              </div>
              
              <div className="results-section">
                <h3>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
                  Section Breakdown
                </h3>
                <ul className="breakdown-list">
                  <li className="breakdown-item">
                    <span className="breakdown-label">Skills</span>
                    <span className="breakdown-value">{results.section_breakdown.skills}%</span>
                  </li>
                  <li className="breakdown-item">
                    <span className="breakdown-label">Experience</span>
                    <span className="breakdown-value">{results.section_breakdown.experience}%</span>
                  </li>
                  <li className="breakdown-item">
                    <span className="breakdown-label">Education</span>
                    <span className="breakdown-value">{results.section_breakdown.education}%</span>
                  </li>
                </ul>
              </div>

              <div className="results-section">
                <h3>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>
                  Extracted Entities
                </h3>
                <div style={{ marginBottom: '1.5rem' }}>
                  <p className="breakdown-label" style={{ marginBottom: '0.5rem' }}>JD Skills Needed:</p>
                  <div className="tags-container">
                    {results.extracted_jd_skills && results.extracted_jd_skills.length > 0 ? (
                      results.extracted_jd_skills.map((skill, index) => <span key={index} className="tag">{skill}</span>)
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>None found</span>
                    )}
                  </div>
                </div>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <p className="breakdown-label" style={{ marginBottom: '0.5rem' }}>Candidate Mastered Skills:</p>
                  <div className="tags-container">
                    {results.candidate_mastered_skills && results.candidate_mastered_skills.length > 0 ? (
                      results.candidate_mastered_skills.map((skill, index) => <span key={index} className="tag" style={{background: '#dcfce7', color: '#166534', border: '1px solid #bbf7d0'}}>{skill}</span>)
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>None found</span>
                    )}
                  </div>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <p className="breakdown-label" style={{ marginBottom: '0.5rem' }}>Candidate Learning Skills:</p>
                  <div className="tags-container">
                    {results.candidate_learning_skills && results.candidate_learning_skills.length > 0 ? (
                      results.candidate_learning_skills.map((skill, index) => <span key={index} className="tag" style={{background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a'}}>{skill}</span>)
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>None found</span>
                    )}
                  </div>
                </div>

                {results.red_flags && results.red_flags.length > 0 && (
                  <div>
                    <p className="breakdown-label" style={{ marginBottom: '0.5rem', color: '#dc2626' }}>Red Flags:</p>
                    <div className="tags-container" style={{ flexDirection: 'column' }}>
                      {results.red_flags.map((flag, index) => (
                        <div key={index} className="error-message" style={{ width: '100%', marginTop: '0', padding: '0.75rem', fontSize: '0.9rem' }}>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                          {flag}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

            </div>
          )}
        </div>

      </div>
    </div>
  );
}