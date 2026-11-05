export default function Landing({ onGetStarted, onLogIn }) {
  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="brand">
          <span className="brand-mark">RR</span>
          <span className="brand-name">ResumeRank</span>
        </div>
        <button className="ghost" onClick={onLogIn}>
          Log In
        </button>
      </header>

      <section className="hero">
        <p className="hero-kicker">Candidate screening, not keyword roulette</p>
        <h1>
          Rank resumes by what they actually say, not whether they used your exact words.
        </h1>
        <p className="hero-sub">
          Paste a job description, drop in a batch of resumes, and get back a shortlist
          ordered by semantic similarity (Sentence-BERT), checked against two keyword
          baselines so you can see exactly why each candidate landed where they did.
        </p>
        <div className="hero-actions">
          <button onClick={onGetStarted}>Create a free account</button>
          <button className="secondary" onClick={onLogIn}>
            Log In
          </button>
        </div>
      </section>

      <section className="how-it-works">
        <h2>How it works</h2>
        <ol className="steps-row">
          <li>
            <span className="step-num">1</span>
            <h3>Paste a job description</h3>
            <p>Title and requirements, same as you'd write for any posting.</p>
          </li>
          <li>
            <span className="step-num">2</span>
            <h3>Drop in resumes</h3>
            <p>PDF or DOCX, mixed formats in one batch, as many as you have.</p>
          </li>
          <li>
            <span className="step-num">3</span>
            <h3>Get a ranked shortlist</h3>
            <p>Each candidate scored and ordered, with the reasoning shown, not hidden.</p>
          </li>
        </ol>
      </section>

      <section className="features">
        <div className="feature-card">
          <h3>Semantic matching</h3>
          <p>
            A candidate who wrote "server-side development" instead of "backend
            engineering" still gets found, because the match is on meaning, not
            exact phrasing.
          </p>
        </div>
        <div className="feature-card">
          <h3>Baselines kept honest</h3>
          <p>
            TF-IDF and BM25 scores are shown alongside the semantic score, not buried.
            You can see when keyword overlap and meaning agree, and when they don't.
          </p>
        </div>
        <div className="feature-card">
          <h3>Nothing's a black box</h3>
          <p>
            Expand any candidate to read the resume text the system actually parsed,
            so a ranking is something you can check, not just trust.
          </p>
        </div>
      </section>

      <section className="closing-cta">
        <h2>Start screening in under a minute</h2>
        <button onClick={onGetStarted}>Create a free account</button>
      </section>
    </div>
  );
}
