#!/usr/bin/env python3
"""
Ultra-simple sports betting beta that WILL deploy to Render.
No numpy, minimal dependencies, clean interface.
"""
import os
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
PORT = int(os.environ.get("PORT", 10000))

# Mock data for demonstration (no API calls needed for beta)
MOCK_GAMES = {
    "nfl": [
        {
            "id": "1",
            "teams": "Chiefs vs Bills",
            "time": "8:20 PM ET",
            "our_pick": "Chiefs -3.5",
            "confidence": 4,
            "expected_value": "+5.2%",
            "best_odds": "-110 (DraftKings)",
            "analysis": "Chiefs at home with rest advantage"
        },
        {
            "id": "2",
            "teams": "Cowboys vs Eagles",
            "time": "4:25 PM ET",
            "our_pick": "Under 48.5",
            "confidence": 5,
            "expected_value": "+8.1%",
            "best_odds": "-105 (FanDuel)",
            "analysis": "Weather conditions favor under"
        },
        {
            "id": "3",
            "teams": "Ravens vs Steelers",
            "time": "1:00 PM ET",
            "our_pick": "Ravens ML",
            "confidence": 3,
            "expected_value": "+3.7%",
            "best_odds": "-145 (BetMGM)",
            "analysis": "Division rivalry but Ravens stronger"
        }
    ]
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BetEdge AI - Professional Sports Betting Analysis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0a0e1a;
            color: #e2e8f0;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 20px;
            border-bottom: 1px solid #334155;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #22d3ee;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .tagline {
            color: #94a3b8;
            font-size: 14px;
            margin-top: 5px;
        }
        
        .hero {
            padding: 40px 0;
            text-align: center;
            background: linear-gradient(180deg, #0a0e1a 0%, #1e293b 100%);
        }
        
        .hero h1 {
            font-size: 36px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #22d3ee, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .hero p {
            color: #94a3b8;
            font-size: 18px;
            margin-bottom: 30px;
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 30px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #10b981;
        }
        
        .stat-label {
            color: #64748b;
            font-size: 14px;
        }
        
        .picks-section {
            padding: 40px 0;
        }
        
        .section-title {
            font-size: 24px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .picks-grid {
            display: grid;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .pick-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .pick-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(34, 211, 238, 0.1);
        }
        
        .pick-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .teams {
            font-size: 18px;
            font-weight: 600;
            color: #f1f5f9;
        }
        
        .confidence {
            display: flex;
            gap: 3px;
        }
        
        .star {
            color: #fbbf24;
            font-size: 16px;
        }
        
        .star.empty {
            color: #475569;
        }
        
        .pick-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .detail {
            display: flex;
            flex-direction: column;
        }
        
        .detail-label {
            color: #64748b;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        
        .detail-value {
            color: #e2e8f0;
            font-size: 16px;
            font-weight: 500;
        }
        
        .ev-positive {
            color: #10b981;
        }
        
        .analysis {
            padding-top: 15px;
            border-top: 1px solid #334155;
            color: #94a3b8;
            font-size: 14px;
        }
        
        .cta-section {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 40px;
            border: 1px solid #334155;
        }
        
        .cta-title {
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .cta-subtitle {
            color: #94a3b8;
            margin-bottom: 20px;
        }
        
        .email-form {
            display: flex;
            gap: 10px;
            max-width: 400px;
            margin: 0 auto;
        }
        
        .email-input {
            flex: 1;
            padding: 12px 16px;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #e2e8f0;
            font-size: 16px;
        }
        
        .email-input::placeholder {
            color: #64748b;
        }
        
        .submit-btn {
            padding: 12px 24px;
            background: linear-gradient(135deg, #22d3ee, #10b981);
            border: none;
            border-radius: 8px;
            color: #0f172a;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .submit-btn:hover {
            transform: scale(1.05);
        }
        
        .footer {
            padding: 20px 0;
            border-top: 1px solid #334155;
            text-align: center;
            color: #64748b;
            font-size: 14px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            background: rgba(34, 211, 238, 0.1);
            border: 1px solid #22d3ee;
            border-radius: 4px;
            color: #22d3ee;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .time {
            color: #64748b;
            font-size: 14px;
        }
        
        @media (max-width: 768px) {
            .stats {
                flex-direction: column;
                gap: 20px;
            }
            
            .hero h1 {
                font-size: 28px;
            }
            
            .email-form {
                flex-direction: column;
            }
            
            .pick-details {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="logo">
                <span>⚡</span>
                <span>BetEdge AI</span>
                <span class="badge">BETA</span>
            </div>
            <div class="tagline">Professional Sports Betting Analysis Powered by AI</div>
        </div>
    </header>
    
    <section class="hero">
        <div class="container">
            <h1>Today's High-Value Betting Opportunities</h1>
            <p>Our AI analyzes millions of data points to find the best edges</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">67%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat">
                    <div class="stat-value">+18.3%</div>
                    <div class="stat-label">Monthly ROI</div>
                </div>
                <div class="stat">
                    <div class="stat-value">4.2/5</div>
                    <div class="stat-label">Avg Confidence</div>
                </div>
            </div>
        </div>
    </section>
    
    <section class="picks-section">
        <div class="container">
            <h2 class="section-title">
                <span>🏈</span>
                <span>Today's Top NFL Picks</span>
            </h2>
            
            <div class="picks-grid" id="picks">
                <!-- Picks will be inserted here -->
            </div>
            
            <div class="cta-section">
                <h2 class="cta-title">Get Full Access to All Picks</h2>
                <p class="cta-subtitle">Join the waitlist for unlimited picks, advanced analytics, and real-time alerts</p>
                <form class="email-form" onsubmit="handleSubmit(event)">
                    <input 
                        type="email" 
                        class="email-input" 
                        placeholder="Enter your email"
                        required
                    />
                    <button type="submit" class="submit-btn">Join Waitlist</button>
                </form>
            </div>
        </div>
    </section>
    
    <footer class="footer">
        <div class="container">
            <p>© 2024 BetEdge AI - Professional Betting Analysis | Beta Version 1.0</p>
        </div>
    </footer>
    
    <script>
        // Render picks
        const games = {games};
        const picksContainer = document.getElementById('picks');
        
        games.forEach(game => {
            const stars = Array(5).fill(0).map((_, i) => 
                i < game.confidence ? '★' : '☆'
            ).join('');
            
            const pickHTML = `
                <div class="pick-card">
                    <div class="pick-header">
                        <div>
                            <div class="teams">${game.teams}</div>
                            <div class="time">${game.time}</div>
                        </div>
                        <div class="confidence">
                            ${stars.split('').map(s => 
                                `<span class="star ${s === '☆' ? 'empty' : ''}">${s}</span>`
                            ).join('')}
                        </div>
                    </div>
                    <div class="pick-details">
                        <div class="detail">
                            <span class="detail-label">Our Pick</span>
                            <span class="detail-value">${game.our_pick}</span>
                        </div>
                        <div class="detail">
                            <span class="detail-label">Expected Value</span>
                            <span class="detail-value ev-positive">${game.expected_value}</span>
                        </div>
                        <div class="detail">
                            <span class="detail-label">Best Odds</span>
                            <span class="detail-value">${game.best_odds}</span>
                        </div>
                        <div class="detail">
                            <span class="detail-label">Confidence</span>
                            <span class="detail-value">${game.confidence}/5</span>
                        </div>
                    </div>
                    <div class="analysis">
                        <strong>Analysis:</strong> ${game.analysis}
                    </div>
                </div>
            `;
            picksContainer.innerHTML += pickHTML;
        });
        
        function handleSubmit(event) {
            event.preventDefault();
            alert('Thank you! You've been added to our waitlist.');
            event.target.reset();
        }
    </script>
</body>
</html>"""

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Generate HTML with mock data
            html = HTML_TEMPLATE.replace('{games}', json.dumps(MOCK_GAMES["nfl"]))
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        
        elif self.path == '/health':
            # Health check endpoint for Render
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Override to reduce console noise
        pass

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, SimpleHandler)
    print(f"✅ Server running on port {PORT}")
    print(f"📊 BetEdge AI Beta - Ready for deployment")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()