import { useEffect, useState } from "react";
import { deleteJob, listJobs } from "./api";

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function Dashboard({ token, onNewJob, onOpenJob }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirmingId, setConfirmingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    listJobs(token)
      .then(setJobs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleDeleteClick(e, job) {
    e.stopPropagation();
    if (confirmingId !== job.id) {
      setConfirmingId(job.id);
      return;
    }
    setDeletingId(job.id);
    setError("");
    try {
      await deleteJob(token, job.id);
      setJobs((prev) => prev.filter((j) => j.id !== job.id));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
      setConfirmingId(null);
    }
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h2>Your Screening Jobs</h2>
          <p className="subtitle">Create a job, upload resumes, and get a ranked shortlist.</p>
        </div>
        <button onClick={onNewJob}>+ New Job</button>
      </div>

      {error && <div className="error">{error}</div>}

      {loading && <p className="muted">Loading your jobs...</p>}

      {!loading && jobs.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon" aria-hidden="true">
            📋
          </div>
          <h3>No jobs yet</h3>
          <p className="muted">
            Create your first job description to start ranking resumes against it.
          </p>
          <button onClick={onNewJob}>+ New Job</button>
        </div>
      )}

      {!loading && jobs.length > 0 && (
        <div className="job-grid">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="job-card"
              role="button"
              tabIndex={0}
              onClick={() => onOpenJob(job)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") onOpenJob(job);
              }}
            >
              <button
                type="button"
                className={`job-card-delete ${confirmingId === job.id ? "confirming" : ""}`}
                onClick={(e) => handleDeleteClick(e, job)}
                onBlur={() => setConfirmingId(null)}
                disabled={deletingId === job.id}
                aria-label={confirmingId === job.id ? "Confirm delete" : "Delete job"}
              >
                {deletingId === job.id ? "..." : confirmingId === job.id ? "confirm?" : "×"}
              </button>
              <h3>{job.title}</h3>
              <p className="job-card-desc">{job.description}</p>
              <span className="job-card-date">Created {formatDate(job.created_at)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
