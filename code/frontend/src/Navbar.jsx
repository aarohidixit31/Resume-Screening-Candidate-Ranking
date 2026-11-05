export default function Navbar({ email, onLogout }) {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="brand">
          <span className="brand-mark">RS</span>
          <span className="brand-name">ResumeRank</span>
        </div>
        <div className="navbar-user">
          <span className="navbar-email">{email}</span>
          <button className="ghost" onClick={onLogout}>
            Log Out
          </button>
        </div>
      </div>
    </header>
  );
}
