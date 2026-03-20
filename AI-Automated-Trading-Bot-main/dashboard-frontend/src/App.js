import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

// API base URL
const API_BASE_URL = 'http://localhost:8000';

// Login Component
function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_BASE_URL}/token`, 
        new URLSearchParams({
          'username': username,
          'password': password
        }), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      localStorage.setItem('token', response.data.access_token);
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-96">
        <h2 className="text-2xl font-bold text-white mb-6">FinTech LLM Dashboard</h2>
        {error && <div className="bg-red-500 text-white p-2 rounded mb-4">{error}</div>}
        <form onSubmit={handleLogin}>
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">Username</label>
            <input 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              className="w-full p-2 rounded bg-gray-700 text-white"
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-300 mb-2">Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              className="w-full p-2 rounded bg-gray-700 text-white"
              required
            />
          </div>
          <button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
}

// Dashboard Component
function Dashboard() {
  const [cryptoPrice, setCryptoPrice] = useState(null);
  const [trades, setTrades] = useState([]);
  const [news, setNews] = useState([]);
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/';
      return;
    }

    const fetchData = async () => {
      try {
        const headers = {
          'Authorization': `Bearer ${token}`
        };

        // Fetch crypto price
        const priceResponse = await axios.get(`${API_BASE_URL}/market-data/crypto/BTCUSDT`, { headers });
        setCryptoPrice(priceResponse.data);

        // Fetch trade history
        const tradesResponse = await axios.get(`${API_BASE_URL}/trades/history`, { headers });
        setTrades(tradesResponse.data.trades);

        // Fetch news sentiment
        const newsResponse = await axios.get(`${API_BASE_URL}/news/sentiment`, { headers });
        setNews(newsResponse.data.news);

        // Fetch fraud detection
        const fraudResponse = await axios.get(`${API_BASE_URL}/fraud/detection`, { headers });
        setFraudAlerts(fraudResponse.data.suspicious_trades);

        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/';
        }
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white text-2xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <nav className="bg-gray-800 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold">FinTech LLM Dashboard</h1>
          <button 
            onClick={handleLogout}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded"
          >
            Logout
          </button>
        </div>
      </nav>

      <div className="container mx-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Crypto Price Card */}
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-bold mb-4">Bitcoin Price</h2>
            {cryptoPrice && (
              <div className="text-3xl font-bold text-green-400">
                ${cryptoPrice.price.toLocaleString()}
              </div>
            )}
            <div className="text-sm text-gray-400 mt-2">
              Last updated: {cryptoPrice && new Date(cryptoPrice.timestamp).toLocaleString()}
            </div>
          </div>

          {/* Trade History Card */}
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-bold mb-4">Recent Trades</h2>
            {trades.length > 0 ? (
              <div className="overflow-y-auto max-h-60">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-gray-400">
                      <th className="pb-2">Symbol</th>
                      <th className="pb-2">Type</th>
                      <th className="pb-2">Price</th>
                      <th className="pb-2">Quantity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.slice(0, 5).map((trade, index) => (
                      <tr key={index} className="border-t border-gray-700">
                        <td className="py-2">{trade[2]}</td>
                        <td className="py-2">
                          <span className={trade[3] === 'BUY' ? 'text-green-400' : 'text-red-400'}>
                            {trade[3]}
                          </span>
                        </td>
                        <td className="py-2">${parseFloat(trade[4]).toLocaleString()}</td>
                        <td className="py-2">{trade[5]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-gray-400">No trades found</div>
            )}
          </div>

          {/* News Sentiment Card */}
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-bold mb-4">Market Sentiment</h2>
            {news.length > 0 ? (
              <div className="overflow-y-auto max-h-60">
                {news.slice(0, 3).map((item, index) => (
                  <div key={index} className="mb-4 pb-4 border-b border-gray-700">
                    <div className="font-medium">{item.title}</div>
                    <div className={`mt-2 text-sm ${
                      item.sentiment.includes('Positive') ? 'text-green-400' : 
                      item.sentiment.includes('Negative') ? 'text-red-400' : 'text-yellow-400'
                    }`}>
                      {item.sentiment}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-gray-400">No news available</div>
            )}
          </div>

          {/* Fraud Alerts Card */}
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-bold mb-4">Fraud Alerts</h2>
            {fraudAlerts.length > 0 ? (
              <div className="overflow-y-auto max-h-60">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-gray-400">
                      <th className="pb-2">Trader</th>
                      <th className="pb-2">Symbol</th>
                      <th className="pb-2">Quantity</th>
                      <th className="pb-2">Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fraudAlerts.map((alert, index) => (
                      <tr key={index} className="border-t border-gray-700">
                        <td className="py-2">{alert.Trader}</td>
                        <td className="py-2">{alert.Symbol}</td>
                        <td className="py-2 text-red-400">{alert.Quantity}</td>
                        <td className="py-2">${parseFloat(alert.Price).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-gray-400">No fraud alerts detected</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;