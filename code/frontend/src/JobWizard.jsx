import { useEffect, useRef, useState } from "react";
import { createJob, getResults, rankJob, uploadResumes } from "./api";

const STEPS = ["Job Description", "Upload Resumes", "Ranked Results"];
const ACCEPTED = [".pdf", ".docx"];

function isAccepted(file) {
  const name = file.name.toLowerCase();
  return ACCEPTED.some((ext) => name.endsWith(ext));
}

function RankBadge({ rank }) {
  const tier = rank === 1 ? "gold" : rank === 2 ? "silver" : rank === 3 ? "bronze" : "plain";
  const label = rank === 1 ? "top match" : `no. ${rank}`;
  return (
    <span className={`rank-badge rank-${tier}`}>
      <span>{label}</span>
    </span>
  );
}

function ScoreBar({ label, value, max }) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
  return (
    <div className="score-bar">
      <div className="score-bar-label">
        <span>{label}</span>
        <span>{value.toFixed(3)}</span>
      </div>
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function JobWizard({ token, initialJob, onBack }) {
  const [step, setStep] = useState(initialJob ? 1 : 0);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [job, setJob] = useState(initialJob || null);
  const [files, setFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [results, setResults] = useState([]);
  const [checkingExisting, setCheckingExisting] = useState(Boolean(initialJob));
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!initialJob) return;
    getResults(token, initialJob.id)
      .then((existing) => {
        if (existing.length > 0) {
          setResults(existing);
          setStep(2);
        }
      })
      .catch(() => {})
      .finally(() => setCheckingExisting(false));
  }, [initialJob, token]);

  async function handleCreateJob(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const created = await createJob(token, title, description);
      setJob(created);
      setStep(1);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function addFiles(newFiles) {
    const accepted = Array.from(newFiles).filter(isAccepted);
    const rejected = newFiles.length - accepted.length;
    if (rejected > 0) {
      setError(`${rejected} file(s) skipped — only PDF and DOCX are supported.`);
    } else {
      setError("");
    }
    setFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.name));
      const deduped = accepted.filter((f) => !existingNames.has(f.name));
      return [...prev, ...deduped];
    });
  }

  function removeFile(name) {
    setFiles((prev) => prev.filter((f) => f.name !== name));
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragActive(false);
    addFiles(e.dataTransfer.files);
  }

  async function handleUploadResumes() {
    if (files.length === 0) {
      setError("Select at least one PDF or DOCX resume.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await uploadResumes(token, job.id, files);
      setFiles([]);
      await handleRank(job.id);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  async function handleRank(jobId = job.id) {
    setError("");
    setLoading(true);
    try {
      const ranked = await rankJob(token, jobId);
      setResults(ranked);
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const maxTfidf = Math.max(1e-9, ...results.map((r) => r.tfidf_score));
  const maxBm25 = Math.max(1e-9, ...results.map((r) => r.bm25_score));

  return (
    <div className="wizard">
      <button className="back-link" onClick={onBack}>
        &larr; Back to Jobs
      </button>

      <ol className="stepper">
        {STEPS.map((label, i) => (
          <li
            key={label}
            className={i === step ? "active" : i < step ? "done" : ""}
          >
            <span className="stepper-dot">{i < step ? "✓" : i + 1}</span>
            <span className="stepper-label">{label}</span>
          </li>
        ))}
      </ol>

      {error && <div className="error">{error}</div>}

      {step === 0 && (
        <form className="card" onSubmit={handleCreateJob}>
          <label>
            Job title
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Backend Developer"
              required
            />
          </label>
          <label>
            Job description
            <textarea
              rows={8}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Paste the job description / required skills here..."
              required
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Creating..." : "Continue →"}
          </button>
        </form>
      )}

      {step === 1 && job && !checkingExisting && (
        <div className="card">
          <p className="job-context">
            Job: <strong>{job.title}</strong>
          </p>

          <div
            className={`dropzone ${dragActive ? "drag-active" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="dropzone-icon" aria-hidden="true">
              {"⬆️"}
            </div>
            <p>
              <strong>Drag &amp; drop resumes here</strong>, or click to browse
            </p>
            <span className="dropzone-hint">PDF or DOCX &middot; multiple files allowed</span>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx"
              hidden
              onChange={(e) => addFiles(e.target.files)}
            />
          </div>

          {files.length > 0 && (
            <ul className="file-chips">
              {files.map((f) => (
                <li key={f.name} className="file-chip">
                  <span>{f.name}</span>
                  <button
                    type="button"
                    className="chip-remove"
                    onClick={() => removeFile(f.name)}
                    aria-label={`Remove ${f.name}`}
                  >
                    &times;
                  </button>
                </li>
              ))}
            </ul>
          )}

          <button onClick={handleUploadResumes} disabled={loading || files.length === 0}>
            {loading ? "Uploading & Ranking..." : `Upload ${files.length || ""} & Rank →`}
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <div className="results-header">
            <h3>Ranked Candidates</h3>
            <button className="ghost" onClick={() => setStep(1)}>
              + Add more resumes
            </button>
          </div>

          <ol className="result-list">
            {results.map((r) => (
              <li key={r.candidate_id} className="result-card">
                <RankBadge rank={r.rank} />
                <div className="result-body">
                  <span className="result-name">{r.file_name}</span>
                  <ScoreBar label="TF-IDF" value={r.tfidf_score} max={maxTfidf} />
                  <ScoreBar label="BM25" value={r.bm25_score} max={maxBm25} />
                </div>
              </li>
            ))}
          </ol>

          <button className="secondary" onClick={onBack}>
            Back to all jobs
          </button>
        </div>
      )}
    </div>
  );
}
