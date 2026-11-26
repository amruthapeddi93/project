import { useState } from "react";

import Registration from "./registration/Registration";
import Login from "./Login/Login";
import StockSearch from "./stock-search/StockSearch";
import NewsAgent from "./news-agent/NewsAgent";

import "./App.css";

function App() {
  const [showLogin, setShowLogin] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activePage, setActivePage] = useState("stocks");
  const [menuOpen, setMenuOpen] = useState(false);

  const handleRegistrationSuccess = () => {
    setShowLogin(true);
  };

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    setActivePage("stocks");
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setIsLoggedIn(false);
    setShowLogin(true);
    setActivePage("stocks");
    setMenuOpen(false);
  };

  const navigateTo = (page) => {
    setActivePage(page);
    setMenuOpen(false);
  };

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="brand">
          <h2>
            Stock<span>Research</span>
          </h2>
        </div>

        {!isLoggedIn ? (
          <div className="nav-buttons">
            <button
              className={!showLogin ? "active" : ""}
              onClick={() => setShowLogin(false)}
            >
              Register
            </button>

            <button
              className={showLogin ? "active" : ""}
              onClick={() => setShowLogin(true)}
            >
              Login
            </button>
          </div>
        ) : (
          <div className="nav-menu-container">
            <button
              className="hamburger-button"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Open navigation menu"
              aria-expanded={menuOpen}
            >
              {menuOpen ? "✕" : "☰"}
            </button>

            {menuOpen && (
              <div className="dropdown-menu">
                <button
                  className={activePage === "stocks" ? "selected" : ""}
                  onClick={() => navigateTo("stocks")}
                >
                  Stock Research
                </button>

                <button
                  className={activePage === "news" ? "selected" : ""}
                  onClick={() => navigateTo("news")}
                >
                  News & Sentiment
                </button>

                <button onClick={handleLogout}>Logout</button>
              </div>
            )}
          </div>
        )}
      </nav>

      <main className="main-content">
        {isLoggedIn ? (
          activePage === "stocks" ? (
            <StockSearch />
          ) : (
            <NewsAgent />
          )
        ) : (
          <>
            <div className="welcome-section">
              <h1>Welcome to Smart Stock Research</h1>

              <p>
                Make smarter investment decisions with AI-powered stock analysis
                and insights.
              </p>
            </div>

            <div className="form-section">
              {showLogin ? (
                <Login onLoginSuccess={handleLoginSuccess} />
              ) : (
                <Registration
                  onRegistrationSuccess={handleRegistrationSuccess}
                />
              )}
            </div>
          </>
        )}
      </main>

      <footer className="footer">
        © 2026 AI-Powered Stock Research System
      </footer>
    </div>
  );
}

export default App;
