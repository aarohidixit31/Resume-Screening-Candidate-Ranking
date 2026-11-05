import { useEffect, useState } from "react";
import { listJobs } from "./api";

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

  useEffect(() => {
    listJobs(token)
      .then(setJobs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

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
            <button key={job.id} className="job-card" onClick={() => onOpenJob(job)}>
              <h3>{job.title}</h3>
              <p className="job-card-desc">{job.description}</p>
              <span className="job-card-date">Created {formatDate(job.created_at)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
