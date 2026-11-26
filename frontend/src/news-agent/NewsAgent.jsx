import { useState } from "react";
import { getStockNews } from "../services/newsService";
import "./NewsAgent.css";

function NewsAgent({ symbol: initialSymbol, market: initialMarket }) {
  const [symbol, setSymbol] = useState(initialSymbol || "AAPL");
  const [market, setMarket] = useState(initialMarket || "us");

  const [news, setNews] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchNews = async () => {
    if (!symbol.trim()) {
      setError("Stock symbol is required.");
      return;
    }

    setLoading(true);
    setError("");
    setNews(null);

    try {
      const result = await getStockNews(symbol.trim(), market);
      setNews(result);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to fetch stock news.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="news-container">
      <h2>News & Sentiment Analysis</h2>

      <p className="news-description">
        Latest news and AI-powered sentiment analysis for {symbol}.
      </p>

      <div className="news-controls">
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Enter stock symbol"
        />

        <select value={market} onChange={(e) => setMarket(e.target.value)}>
          <option value="us">US Market</option>
          <option value="india">Indian Market</option>
        </select>

        <button onClick={fetchNews} disabled={loading}>
          {loading ? "Analyzing..." : "Get Stock News"}
        </button>
      </div>

      {error && <p className="news-error">{error}</p>}

      {loading && (
        <p className="news-loading">Fetching news and analyzing sentiment...</p>
      )}

      {news && (
        <div className="news-results">
          <div className="news-overview">
            <h3>{news.symbol} News Overview</h3>
            <p>Market: {news.market?.toUpperCase()}</p>
            <p>Articles found: {news.article_count}</p>
          </div>

          <div className="sentiment-section">
            <h3>AI Sentiment Analysis</h3>

            {news.ai_analysis ? (
              <div className="analysis-card">
                <h4>
                  Overall Sentiment:{" "}
                  {news.ai_analysis.overall_sentiment?.toUpperCase() || "N/A"}
                </h4>

                <p>{news.ai_analysis.summary}</p>

                <h4>Key Events</h4>
                {news.ai_analysis.key_events?.length > 0 ? (
                  <ul>
                    {news.ai_analysis.key_events.map((event, index) => (
                      <li key={index}>{event}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No key events available.</p>
                )}

                <h4>Possible Impact</h4>
                <p>{news.ai_analysis.possible_impact || "Not available."}</p>

                <h4>Uncertainties</h4>
                {news.ai_analysis.uncertainties?.length > 0 ? (
                  <ul>
                    {news.ai_analysis.uncertainties.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No uncertainties reported.</p>
                )}

                <h4>Article Assessments</h4>
                {news.ai_analysis.article_assessments?.length > 0 ? (
                  news.ai_analysis.article_assessments.map((item, index) => (
                    <div className="assessment-card" key={index}>
                      <strong>{item.title}</strong>
                      <p>Sentiment: {item.sentiment || "N/A"}</p>
                      <p>{item.reason}</p>

                      {item.source_url && (
                        <a
                          href={item.source_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Read Article
                        </a>
                      )}
                    </div>
                  ))
                ) : (
                  <p>No individual article assessments available.</p>
                )}
              </div>
            ) : (
              <div className="analysis-unavailable">
                <p>AI analysis is currently unavailable.</p>
                <p>
                  {news.message ||
                    news.ai_analysis_status ||
                    "Please try again later."}
                </p>
                <p>The news articles may still be available below.</p>
              </div>
            )}
          </div>

          <div className="articles-section">
            <h3>Latest News Articles</h3>

            {news.articles?.length > 0 ? (
              news.articles.map((article, index) => (
                <article className="article-card" key={article.url || index}>
                  <h4>{article.title}</h4>

                  <p>
                    {article.description ||
                      article.snippet ||
                      "No description available."}
                  </p>

                  <small>
                    {article.source || "Unknown source"}
                    {" | "}
                    {article.published_at || "Date unavailable"}
                  </small>

                  {article.url && (
                    <p>
                      <a href={article.url} target="_blank" rel="noreferrer">
                        Read Full Article
                      </a>
                    </p>
                  )}
                </article>
              ))
            ) : (
              <p>No news articles found for this stock.</p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

export default NewsAgent;
