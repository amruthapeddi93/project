const API_BASE_URL = "http://127.0.0.1:8000";

export async function getStockNews(symbol, market) {
  const response = await fetch(
    `${API_BASE_URL}/api/news/${encodeURIComponent(symbol)}?market=${encodeURIComponent(market)}`,
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Unable to fetch stock news");
  }

  return data;
}
