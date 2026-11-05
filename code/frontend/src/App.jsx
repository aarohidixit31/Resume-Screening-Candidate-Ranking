import { useEffect, useState } from "react";
import "./App.css";
import AuthForm from "./AuthForm";
import Dashboard from "./Dashboard";
import JobWizard from "./JobWizard";
import Navbar from "./Navbar";
import { getMe } from "./api";

const TOKEN_KEY = "resume_screener_token";

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(Boolean(token));
  const [view, setView] = useState("dashboard"); // "dashboard" | "wizard"
  const [activeJob, setActiveJob] = useState(null);
  const [dashboardKey, setDashboardKey] = useState(0);

  useEffect(() => {
    if (!token) {
      setCheckingSession(false);
      return;
    }
    getMe(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => setCheckingSession(false));
  }, [token]);

  function handleAuthenticated(newToken) {
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    setView("dashboard");
    setActiveJob(null);
  }

  function openNewJob() {
    setActiveJob(null);
    setView("wizard");
  }

  function openExistingJob(job) {
    setActiveJob(job);
    setView("wizard");
  }

  function backToDashboard() {
    setView("dashboard");
    setActiveJob(null);
    setDashboardKey((k) => k + 1); // refetch job list in case a new job was created
  }

  if (checkingSession) {
    return <div className="page">Loading...</div>;
  }

  if (!token) {
    return <AuthForm onAuthenticated={handleAuthenticated} />;
  }

  return (
    <>
      <Navbar email={user?.email} onLogout={handleLogout} />
      <div className="page">
        {view === "dashboard" && (
          <Dashboard
            key={dashboardKey}
            token={token}
            onNewJob={openNewJob}
            onOpenJob={openExistingJob}
          />
        )}
        {view === "wizard" && (
          <JobWizard token={token} initialJob={activeJob} onBack={backToDashboard} />
        )}
      </div>
    </>
  );
}
