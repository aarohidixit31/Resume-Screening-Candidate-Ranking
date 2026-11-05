import { useState } from "react";
import { login, signup } from "./api";

export default function AuthForm({ initialMode = "login", onAuthenticated, onBack }) {
  const [mode, setMode] = useState(initialMode); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const action = mode === "login" ? login : signup;
      const { access_token } = await action(email, password);
      onAuthenticated(access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page auth-page">
      <button className="back-link" onClick={onBack}>
        &larr; Back
      </button>

      <header className="header">
        <h1>Resume Screening &amp; Candidate Ranking</h1>
        <p className="subtitle">Sign in to create jobs and rank candidates</p>
      </header>

      <form className="card" onSubmit={handleSubmit}>
        <div className="auth-tabs">
          <button
            type="button"
            className={mode === "login" ? "tab active" : "tab"}
            onClick={() => setMode("login")}
          >
            Log In
          </button>
          <button
            type="button"
            className={mode === "signup" ? "tab active" : "tab"}
            onClick={() => setMode("signup")}
          >
            Sign Up
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Please wait..." : mode === "login" ? "Log In" : "Create Account"}
        </button>
      </form>
    </div>
  );
}
