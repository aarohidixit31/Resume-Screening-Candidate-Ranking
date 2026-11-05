const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg).join(", ")
      : detail || body.error || `Request failed (${res.status})`;
    throw new Error(message);
  }
  if (res.status === 204) return null;
  return res.json();
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

// --- Auth ---
export function signup(email, password) {
  return fetch(`${BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  }).then(handle);
}

export function login(email, password) {
  return fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  }).then(handle);
}

export function getMe(token) {
  return fetch(`${BASE_URL}/auth/me`, { headers: authHeaders(token) }).then(handle);
}

// --- Jobs ---
export function listJobs(token) {
  return fetch(`${BASE_URL}/jobs`, { headers: authHeaders(token) }).then(handle);
}

export function createJob(token, title, description) {
  return fetch(`${BASE_URL}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ title, description }),
  }).then(handle);
}

export function uploadResumes(token, jobId, files) {
  const form = new FormData();
  for (const file of files) form.append("files", file);
  return fetch(`${BASE_URL}/jobs/${jobId}/resumes`, {
    method: "POST",
    headers: authHeaders(token),
    body: form,
  }).then(handle);
}

export function rankJob(token, jobId) {
  return fetch(`${BASE_URL}/jobs/${jobId}/rank`, {
    method: "POST",
    headers: authHeaders(token),
  }).then(handle);
}

export function getResults(token, jobId) {
  return fetch(`${BASE_URL}/jobs/${jobId}/results`, { headers: authHeaders(token) }).then(handle);
}

export function deleteJob(token, jobId) {
  return fetch(`${BASE_URL}/jobs/${jobId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  }).then(handle);
}

export function updateJob(token, jobId, data) {
  return fetch(`${BASE_URL}/jobs/${jobId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify(data),
  }).then(handle);
}

// --- Candidates ---
export function getCandidate(token, candidateId) {
  return fetch(`${BASE_URL}/candidates/${candidateId}`, { headers: authHeaders(token) }).then(handle);
}
