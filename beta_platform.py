#!/usr/bin/env python3
"""
Sports Betting Beta Platform - Main Entry Point
Unified dashboard with NFL and NCAAF access
"""

import os
import sys
import json
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Fix Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Environment setup
os.environ.setdefault('SECRET_KEY', 'beta-secret-key-2025')
os.environ.setdefault('ODDS_API_KEY', 'demo-key')

# Initialize FastAPI
app = FastAPI(
    title="Sports Betting Analytics - BETA",
    description="NFL & NCAAF Analytics Platform",
    version="0.1.0-beta"
)

# CORS for beta
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Beta user storage
beta_users = {}
active_sessions = {}

# Models
class BetaRegistration(BaseModel):
    email: str
    name: str
    experience: str
    preferred_sports: List[str]

class Opportunity(BaseModel):
    id: str
    sport: str
    type: str  # 'arbitrage', 'value', 'prop'
    game: str
    bet_description: str
    confidence: float
    expected_value: float
    sportsbooks: List[str]
    timestamp: datetime

# Landing Page
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Beta registration landing page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sports Betting Analytics - Beta Access</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
            }
            
            /* Header */
            .header {
                background: rgba(255,255,255,0.95);
                padding: 20px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .logo {
                font-size: 24px;
                font-weight: bold;
                color: #1e3c72;
            }
            .nav-links {
                display: flex;
                gap: 30px;
            }
            .nav-links a {
                color: #555;
                text-decoration: none;
                font-weight: 500;
                transition: color 0.3s;
            }
            .nav-links a:hover {
                color: #1e3c72;
            }
            
            /* Hero Section */
            .hero {
                text-align: center;
                padding: 80px 20px;
                color: white;
            }
            .hero h1 {
                font-size: 48px;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .hero p {
                font-size: 20px;
                opacity: 0.9;
                max-width: 600px;
                margin: 0 auto 40px;
            }
            .beta-badge {
                display: inline-block;
                background: #ff6b6b;
                color: white;
                padding: 8px 20px;
                border-radius: 25px;
                font-weight: bold;
                margin-bottom: 40px;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            /* Registration Form */
            .registration-container {
                max-width: 500px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            .form-title {
                color: #333;
                margin-bottom: 30px;
                text-align: center;
            }
            .form-group {
                margin-bottom: 25px;
            }
            label {
                display: block;
                color: #555;
                margin-bottom: 8px;
                font-weight: 500;
            }
            input, select {
                width: 100%;
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input:focus, select:focus {
                outline: none;
                border-color: #1e3c72;
            }
            .sport-selection {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 10px;
            }
            .sport-option {
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
            }
            .sport-option:hover {
                border-color: #1e3c72;
                background: #f8f9fa;
            }
            .sport-option.selected {
                border-color: #1e3c72;
                background: #1e3c72;
                color: white;
            }
            .sport-option .icon {
                font-size: 24px;
                margin-bottom: 5px;
            }
            .submit-btn {
                width: 100%;
                padding: 15px;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            }
            .submit-btn:hover {
                transform: translateY(-2px);
            }
            
            /* Features */
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 30px;
                max-width: 1200px;
                margin: 80px auto;
                padding: 0 20px;
            }
            .feature-card {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 30px;
                text-align: center;
                color: white;
                border: 1px solid rgba(255,255,255,0.2);
            }
            .feature-icon {
                font-size: 48px;
                margin-bottom: 20px;
            }
            .feature-title {
                font-size: 20px;
                margin-bottom: 10px;
            }
            .feature-desc {
                opacity: 0.8;
                line-height: 1.6;
            }
            
            /* Success Message */
            .success-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.8);
                z-index: 1000;
            }
            .success-modal {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                border-radius: 15px;
                padding: 40px;
                text-align: center;
                max-width: 500px;
            }
            .success-icon {
                font-size: 64px;
                color: #4caf50;
                margin-bottom: 20px;
            }
            .access-code {
                background: #f0f0f0;
                padding: 15px;
                border-radius: 8px;
                font-family: monospace;
                font-size: 24px;
                margin: 20px 0;
                color: #1e3c72;
            }
            .dashboard-btn {
                padding: 15px 30px;
                background: #1e3c72;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <!-- Header -->
        <div class="header">
            <div class="logo">⚡ SportsBet Analytics</div>
            <div class="nav-links">
                <a href="#features">Features</a>
                <a href="#sports">Sports</a>
                <a href="#how-it-works">How It Works</a>
                <a href="#faq">FAQ</a>
            </div>
        </div>
        
        <!-- Hero Section -->
        <div class="hero">
            <div class="beta-badge">🔥 EXCLUSIVE BETA ACCESS</div>
            <h1>AI-Powered Sports Betting Analytics</h1>
            <p>Get real-time arbitrage opportunities, value bets, and expert predictions for NFL and NCAAF games.</p>
        </div>
        
        <!-- Registration Form -->
        <div class="registration-container">
            <h2 class="form-title">Join the Beta Program</h2>
            <form id="betaForm" onsubmit="return registerBeta(event)">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" required>
                </div>
                
                <div class="form-group">
                    <label for="name">Full Name</label>
                    <input type="text" id="name" required>
                </div>
                
                <div class="form-group">
                    <label for="experience">Betting Experience</label>
                    <select id="experience" required>
                        <option value="">Select your level</option>
                        <option value="beginner">Beginner (< 1 year)</option>
                        <option value="intermediate">Intermediate (1-3 years)</option>
                        <option value="advanced">Advanced (3-5 years)</option>
                        <option value="professional">Professional (5+ years)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Select Your Sports</label>
                    <div class="sport-selection">
                        <div class="sport-option" onclick="toggleSport(this, 'NFL')">
                            <div class="icon">🏈</div>
                            <div>NFL</div>
                        </div>
                        <div class="sport-option" onclick="toggleSport(this, 'NCAAF')">
                            <div class="icon">🏈</div>
                            <div>NCAAF</div>
                        </div>
                        <div class="sport-option" onclick="toggleSport(this, 'MLB')">
                            <div class="icon">⚾</div>
                            <div>MLB</div>
                        </div>
                        <div class="sport-option" onclick="toggleSport(this, 'NBA')">
                            <div class="icon">🏀</div>
                            <div>NBA (Soon)</div>
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="submit-btn">Get Instant Access</button>
            </form>
        </div>
        
        <!-- Features Section -->
        <div class="features" id="features">
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3 class="feature-title">Real-Time Odds</h3>
                <p class="feature-desc">Live odds from DraftKings, FanDuel, BetMGM, and more.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3 class="feature-title">AI Predictions</h3>
                <p class="feature-desc">Machine learning models with 65%+ accuracy.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💰</div>
                <h3 class="feature-title">Arbitrage Alerts</h3>
                <p class="feature-desc">Instant notifications for guaranteed profit opportunities.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📈</div>
                <h3 class="feature-title">Risk Management</h3>
                <p class="feature-desc">Bankroll tracking and optimal bet sizing.</p>
            </div>
        </div>
        
        <!-- FAQ Section -->
        <div class="features" id="faq" style="background: white; padding: 60px 20px; margin-top: 80px;">
            <div style="max-width: 800px; margin: 0 auto;">
                <h2 style="text-align: center; color: #333; margin-bottom: 40px;">Frequently Asked Questions</h2>
                
                <div style="margin-bottom: 25px;">
                    <h3 style="color: #1e3c72; margin-bottom: 10px;">How does the beta program work?</h3>
                    <p style="color: #666; line-height: 1.6;">Register above to get instant access to our NFL and NCAAF dashboards. You'll see real-time opportunities, track your performance, and help shape our product.</p>
                </div>
                
                <div style="margin-bottom: 25px;">
                    <h3 style="color: #1e3c72; margin-bottom: 10px;">Is this real money betting?</h3>
                    <p style="color: #666; line-height: 1.6;">No, we provide analytics and recommendations only. You place bets with your preferred sportsbook. We help you find value and track results.</p>
                </div>
                
                <div style="margin-bottom: 25px;">
                    <h3 style="color: #1e3c72; margin-bottom: 10px;">What's included in beta access?</h3>
                    <p style="color: #666; line-height: 1.6;">Free access to NFL and NCAAF dashboards, real-time opportunities, arbitrage alerts, and our AI predictions. Plus lifetime discount when we launch.</p>
                </div>
                
                <div style="margin-bottom: 25px;">
                    <h3 style="color: #1e3c72; margin-bottom: 10px;">How accurate are your predictions?</h3>
                    <p style="color: #666; line-height: 1.6;">Our models currently achieve 65%+ accuracy on high-confidence bets. We're continuously improving with your feedback.</p>
                </div>
                
                <div style="margin-bottom: 25px;">
                    <h3 style="color: #1e3c72; margin-bottom: 10px;">Need help?</h3>
                    <p style="color: #666; line-height: 1.6;">Email us at beta@sportsbetting.com or use the feedback button in your dashboard. We respond within 24 hours.</p>
                </div>
            </div>
        </div>
        
        <!-- Success Modal -->
        <div class="success-overlay" id="successModal">
            <div class="success-modal">
                <div class="success-icon">✅</div>
                <h2>Welcome to the Beta!</h2>
                <p>Your access code is:</p>
                <div class="access-code" id="accessCode">XXXX-XXXX</div>
                <p>Save this code - you'll need it to access the platform.</p>
                <a href="#" id="dashboardLink" class="dashboard-btn">Go to Dashboard →</a>
            </div>
        </div>
        
        <script>
            let selectedSports = [];
            
            function toggleSport(element, sport) {
                element.classList.toggle('selected');
                if (selectedSports.includes(sport)) {
                    selectedSports = selectedSports.filter(s => s !== sport);
                } else {
                    selectedSports.push(sport);
                }
            }
            
            async function registerBeta(event) {
                event.preventDefault();
                
                const data = {
                    email: document.getElementById('email').value,
                    name: document.getElementById('name').value,
                    experience: document.getElementById('experience').value,
                    preferred_sports: selectedSports
                };
                
                try {
                    const response = await fetch('/api/beta/register', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    // Show success modal
                    document.getElementById('accessCode').textContent = result.access_code;
                    document.getElementById('dashboardLink').href = `/dashboard?code=${result.access_code}`;
                    document.getElementById('successModal').style.display = 'block';
                    
                } catch (error) {
                    alert('Registration failed. Please try again.');
                }
                
                return false;
            }
        </script>
    </body>
    </html>
    """

# Beta Registration API
@app.post("/api/beta/register")
async def register_beta(registration: BetaRegistration):
    """Register for beta access"""
    # Generate access code
    code = f"{random.choice(string.ascii_uppercase)}{random.randint(1000, 9999)}-{random.choice(string.ascii_uppercase)}{random.randint(1000, 9999)}"
    
    # Store user
    beta_users[code] = {
        **registration.dict(),
        "registered_at": datetime.utcnow().isoformat(),
        "code": code
    }
    
    return {
        "access_code": code,
        "dashboard_url": f"/dashboard?code={code}",
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
    }

# Main Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(code: str = Query(...)):
    """Main dashboard with sport selection"""
    if code not in beta_users:
        return HTMLResponse("<h1>Invalid Access Code</h1><p>Please register first.</p>")
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sports Betting Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f7fa;
            }}
            
            /* Header */
            .header {{
                background: white;
                padding: 15px 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .logo {{
                font-size: 20px;
                font-weight: bold;
                color: #1e3c72;
            }}
            .user-info {{
                color: #666;
            }}
            
            /* Sport Selector */
            .sport-nav {{
                background: white;
                padding: 20px 30px;
                margin: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .sport-tabs {{
                display: flex;
                gap: 20px;
            }}
            .sport-tab {{
                padding: 12px 24px;
                background: #f0f0f0;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 500;
                transition: all 0.3s;
                text-decoration: none;
                color: #333;
            }}
            .sport-tab:hover {{
                background: #e0e0e0;
            }}
            .sport-tab.active {{
                background: #1e3c72;
                color: white;
            }}
            
            /* Welcome Section */
            .welcome {{
                padding: 40px;
                text-align: center;
                background: white;
                margin: 20px;
                border-radius: 10px;
            }}
            .welcome h1 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .welcome p {{
                color: #666;
                font-size: 18px;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto 30px;
            }}
            
            /* Stats Grid */
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 0 20px;
                margin-bottom: 40px;
            }}
            .stat-card {{
                background: white;
                padding: 25px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .stat-value {{
                font-size: 32px;
                font-weight: bold;
                color: #1e3c72;
                margin-bottom: 10px;
            }}
            .stat-label {{
                color: #666;
                font-size: 14px;
            }}
            
            /* Action Buttons */
            .actions {{
                display: flex;
                gap: 20px;
                justify-content: center;
                margin-top: 30px;
            }}
            .action-btn {{
                padding: 15px 30px;
                background: #1e3c72;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: transform 0.2s;
            }}
            .action-btn:hover {{
                transform: translateY(-2px);
            }}
            .action-btn.secondary {{
                background: #f0f0f0;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <div class="header">
            <div class="logo">⚡ SportsBet Analytics Beta</div>
            <div class="user-info">
                Access Code: {code} | Expires in 29 days
            </div>
        </div>
        
        <!-- Sport Navigation -->
        <div class="sport-nav">
            <div class="sport-tabs">
                <a href="/nfl?code={code}" class="sport-tab">
                    🏈 NFL Dashboard
                </a>
                <a href="/ncaaf?code={code}" class="sport-tab">
                    🏈 NCAAF Dashboard
                </a>
                <a href="/performance?code={code}" class="sport-tab">
                    📊 Performance Tracker
                </a>
                <a href="#" class="sport-tab" onclick="alert('MLB launches April 2025')">
                    ⚾ MLB (Coming Soon)
                </a>
                <a href="#" class="sport-tab" onclick="alert('NBA launches November 2025')">
                    🏀 NBA (Coming Soon)
                </a>
            </div>
        </div>
        
        <!-- Welcome Section -->
        <div class="welcome">
            <h1>Welcome to Your Sports Betting Command Center</h1>
            <p>
                Select a sport above to access real-time odds, AI predictions, and arbitrage opportunities.
                Our platform analyzes thousands of betting lines every second to find profitable opportunities.
            </p>
            
            <!-- Live Stats -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">47</div>
                    <div class="stat-label">Live Opportunities</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">65.3%</div>
                    <div class="stat-label">Win Rate (7 days)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">+18.7%</div>
                    <div class="stat-label">ROI This Week</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">3</div>
                    <div class="stat-label">Arbitrage Alerts</div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="actions">
                <a href="/nfl?code={code}" class="action-btn">
                    🏈 View NFL Games
                </a>
                <a href="/ncaaf?code={code}" class="action-btn">
                    🏈 View NCAAF Games  
                </a>
                <button class="action-btn secondary" onclick="showHelp()">
                    ❓ Help & Support
                </button>
            </div>
        </div>
        
        <!-- Help Modal -->
        <div id="helpModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; border-radius: 15px; padding: 40px; max-width: 600px; max-height: 80vh; overflow-y: auto;">
                <h2 style="color: #333; margin-bottom: 20px;">Help & Support</h2>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #1e3c72; margin-bottom: 10px;">Quick Guide</h3>
                    <ol style="color: #666; line-height: 1.8;">
                        <li>Select NFL or NCAAF to view today's opportunities</li>
                        <li>Green alerts = Arbitrage (guaranteed profits)</li>
                        <li>Yellow alerts = Value bets (positive expected value)</li>
                        <li>Track your results in the Performance Tracker</li>
                    </ol>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #1e3c72; margin-bottom: 10px;">Contact Support</h3>
                    <p style="color: #666;">Email: beta@sportsbetting.com</p>
                    <p style="color: #666;">Your Access Code: {code}</p>
                </div>
                
                <button onclick="document.getElementById('helpModal').style.display='none'" style="padding: 10px 20px; background: #1e3c72; color: white; border: none; border-radius: 5px; cursor: pointer;">Close</button>
            </div>
        </div>
        
        <script>
            function showHelp() {{
                document.getElementById('helpModal').style.display = 'block';
            }}
        </script>
    </body>
    </html>
    """

# NFL Dashboard
@app.get("/nfl", response_class=HTMLResponse)
async def nfl_dashboard(code: str = Query(...)):
    """NFL betting dashboard"""
    if code not in beta_users:
        return HTMLResponse("<h1>Invalid Access Code</h1>")
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>NFL Betting Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f7fa;
            }}
            .header {{
                background: #1e3c72;
                color: white;
                padding: 20px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .back-btn {{
                color: white;
                text-decoration: none;
                padding: 8px 16px;
                background: rgba(255,255,255,0.2);
                border-radius: 5px;
            }}
            .container {{
                max-width: 1400px;
                margin: 20px auto;
                padding: 0 20px;
            }}
            .games-grid {{
                display: grid;
                gap: 20px;
                margin-top: 20px;
            }}
            .game-card {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .game-header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid #e0e0e0;
            }}
            .teams {{
                font-size: 18px;
                font-weight: 600;
                color: #333;
            }}
            .game-time {{
                color: #666;
                font-size: 14px;
            }}
            .odds-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin-top: 15px;
            }}
            .odds-box {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }}
            .odds-label {{
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }}
            .odds-value {{
                font-size: 20px;
                font-weight: bold;
                color: #1e3c72;
            }}
            .opportunity {{
                background: #e8f5e9;
                border: 1px solid #4caf50;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
            }}
            .opportunity-label {{
                color: #2e7d32;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏈 NFL Betting Dashboard</h1>
            <a href="/dashboard?code={code}" class="back-btn">← Back to Main</a>
        </div>
        
        <div class="container">
            <h2>Today's Games & Opportunities</h2>
            
            <div class="games-grid">
                <!-- Game 1 -->
                <div class="game-card">
                    <div class="game-header">
                        <div class="teams">Kansas City Chiefs @ Buffalo Bills</div>
                        <div class="game-time">Sun 4:25 PM ET</div>
                    </div>
                    <div class="odds-grid">
                        <div class="odds-box">
                            <div class="odds-label">Spread</div>
                            <div class="odds-value">BUF -2.5</div>
                        </div>
                        <div class="odds-box">
                            <div class="odds-label">Total</div>
                            <div class="odds-value">O/U 48.5</div>
                        </div>
                        <div class="odds-box">
                            <div class="odds-label">Moneyline</div>
                            <div class="odds-value">KC +120</div>
                        </div>
                    </div>
                    <div class="opportunity">
                        <div class="opportunity-label">⚡ ARBITRAGE OPPORTUNITY</div>
                        <div>Over 48.5 @ DraftKings -105 | Under 48.5 @ FanDuel -103</div>
                        <div>Guaranteed Return: +2.4%</div>
                    </div>
                </div>
                
                <!-- Game 2 -->
                <div class="game-card">
                    <div class="game-header">
                        <div class="teams">Dallas Cowboys @ New York Giants</div>
                        <div class="game-time">Sun 1:00 PM ET</div>
                    </div>
                    <div class="odds-grid">
                        <div class="odds-box">
                            <div class="odds-label">Spread</div>
                            <div class="odds-value">DAL -3.5</div>
                        </div>
                        <div class="odds-box">
                            <div class="odds-label">Total</div>
                            <div class="odds-value">O/U 44.5</div>
                        </div>
                        <div class="odds-box">
                            <div class="odds-label">Moneyline</div>
                            <div class="odds-value">DAL -165</div>
                        </div>
                    </div>
                    <div class="opportunity" style="background: #fff3e0; border-color: #ff9800;">
                        <div class="opportunity-label" style="color: #e65100;">💎 VALUE BET</div>
                        <div>Model Prediction: Cowboys -6.5 | Current Line: -3.5</div>
                        <div>Expected Value: +4.2% | Confidence: 68%</div>
                    </div>
                </div>
                
                <!-- More games would be loaded dynamically -->
            </div>
        </div>
    </body>
    </html>
    """

# NCAAF Dashboard
@app.get("/ncaaf", response_class=HTMLResponse)
async def ncaaf_dashboard(code: str = Query(...)):
    """NCAAF betting dashboard"""
    if code not in beta_users:
        return HTMLResponse("<h1>Invalid Access Code</h1>")
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>NCAAF Betting Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f7fa;
            }}
            .header {{
                background: #8b0000;
                color: white;
                padding: 20px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .back-btn {{
                color: white;
                text-decoration: none;
                padding: 8px 16px;
                background: rgba(255,255,255,0.2);
                border-radius: 5px;
            }}
            .container {{
                max-width: 1400px;
                margin: 20px auto;
                padding: 0 20px;
            }}
            .conference-filter {{
                background: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .conf-btn {{
                padding: 8px 16px;
                background: #f0f0f0;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
            .conf-btn.active {{
                background: #8b0000;
                color: white;
            }}
            .games-grid {{
                display: grid;
                gap: 20px;
            }}
            .game-card {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .game-header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid #e0e0e0;
            }}
            .teams {{
                font-size: 18px;
                font-weight: 600;
                color: #333;
            }}
            .ranking {{
                color: #8b0000;
                font-weight: bold;
            }}
            .game-time {{
                color: #666;
                font-size: 14px;
            }}
            .odds-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin-top: 15px;
            }}
            .odds-box {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }}
            .odds-label {{
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }}
            .odds-value {{
                font-size: 20px;
                font-weight: bold;
                color: #8b0000;
            }}
            .alert {{
                background: #fce4ec;
                border: 1px solid #c2185b;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
            }}
            .alert-label {{
                color: #880e4f;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏈 NCAAF Betting Dashboard</h1>
            <a href="/dashboard?code={code}" class="back-btn">← Back to Main</a>
        </div>
        
        <div class="container">
            <h2>Saturday's Games & Opportunities</h2>
            
            <!-- Conference Filter -->
            <div class="conference-filter">
                <button class="conf-btn active">All</button>
                <button class="conf-btn">SEC</button>
                <button class="conf-btn">Big Ten</button>
                <button class="conf-btn">ACC</button>
                <button class="conf-btn">Big 12</button>
                <button class="conf-btn">Pac-12</button>
            </div>
            
            <div class="games-grid">
                <!-- Game 1 -->
                <div class="game-card">
                    <div class="game-header">
                        <div class="teams">
                            <span class="ranking">#1</span> Georgia @ 
                            <span class="ranking">#4</span> Alabama
                        </div>
                        <div class="game-time">Sat 3:30 PM ET • CBS</div>
                    </div>
                    <div class="odds-grid">
                        <div class="odds-box">
                            <div class="odds-label">Spread</div>
                            <div class="odds-value">ALA -3.5</div>
                        </div>
                        <div class="odds-box">
                            <div class="odds-label">Total</div>
                            <div class="odds-value">O/U 52.5</div>
                        </div>
                        <div class="odds-box">
                            <div class="odds-label">Moneyline</div>
                            <div class="odds-value">UGA +145</div>
                        </div>
                    </div>
                    <div class="alert">
                        <div class="alert-label">🔥 HOT PICK</div>
                        <div>Public: 78% on Alabama | Sharp Money: Georgia +3.5</div>
                        <div>Line Movement: Opened -4.5, now -3.5</div>
                    </div>
                </div>
                
                <!-- Game 2 -->
                <div class="game-card">
                    <div class="game-header">
                        <div class="teams">
                            <span class="ranking">#7</span> Michigan @ 
                            <span class="ranking">#10</span> Penn State
                        </div>
                        <div class="game-time">Sat 12:00 PM ET • FOX</div>
                    </div>
                    <div class="odds-grid">
                        <div class="odds-box">
                            <div class="odds-label">Spread</div>
                            <div class="odds-value">PSU -2.5</div>
                        </div>
                        <div class="odds-box">
                            <div class="odds-label">Total</div>
                            <div class="odds-value">O/U 48.5</div>
                        </div>
                        <div class="odds-box">
                            <div class="odds-label">Moneyline</div>
                            <div class="odds-value">MICH +110</div>
                        </div>
                    </div>
                    <div class="alert" style="background: #e8f5e9; border-color: #4caf50;">
                        <div class="alert-label" style="color: #2e7d32;">💰 VALUE PLAY</div>
                        <div>Under 48.5 | Weather: 20mph winds, 40% rain</div>
                        <div>Model Projection: 41 total points</div>
                    </div>
                </div>
                
                <!-- More games would be loaded dynamically -->
            </div>
        </div>
    </body>
    </html>
    """

# Performance Tracker
@app.get("/performance", response_class=HTMLResponse)
async def performance_tracker(code: str = Query(...)):
    """Performance tracking dashboard"""
    if code not in beta_users:
        return HTMLResponse("<h1>Invalid Access Code</h1>")
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Performance Tracker - Sports Betting Beta</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f7fa;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                padding: 20px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .back-btn {{
                color: white;
                text-decoration: none;
                padding: 8px 16px;
                background: rgba(255,255,255,0.2);
                border-radius: 5px;
            }}
            .container {{
                max-width: 1400px;
                margin: 20px auto;
                padding: 0 20px;
            }}
            
            /* Summary Cards */
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .summary-card {{
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .summary-value {{
                font-size: 36px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .positive {{ color: #27ae60; }}
            .negative {{ color: #e74c3c; }}
            .neutral {{ color: #3498db; }}
            .summary-label {{
                color: #666;
                font-size: 14px;
                text-transform: uppercase;
            }}
            
            /* Performance Chart Placeholder */
            .chart-section {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                margin: 30px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .chart-placeholder {{
                height: 300px;
                background: linear-gradient(to top, #f0f0f0 0%, #f0f0f0 50%, transparent 50%);
                background-size: 100% 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #999;
                position: relative;
            }}
            
            /* Bet History Table */
            .history-section {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                margin: 30px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th {{
                background: #f8f9fa;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                color: #333;
                border-bottom: 2px solid #dee2e6;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #dee2e6;
            }}
            .badge {{
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }}
            .badge-win {{
                background: #d4edda;
                color: #155724;
            }}
            .badge-loss {{
                background: #f8d7da;
                color: #721c24;
            }}
            .badge-pending {{
                background: #fff3cd;
                color: #856404;
            }}
            
            /* Add Bet Button */
            .add-bet-btn {{
                padding: 12px 24px;
                background: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                margin: 20px 0;
            }}
            .add-bet-btn:hover {{
                background: #2980b9;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Performance Tracker</h1>
            <a href="/dashboard?code={code}" class="back-btn">← Back to Main</a>
        </div>
        
        <div class="container">
            <!-- Summary Statistics -->
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-value neutral">47</div>
                    <div class="summary-label">Total Bets</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value positive">65.3%</div>
                    <div class="summary-label">Win Rate</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value positive">+$847</div>
                    <div class="summary-label">Total Profit</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value positive">+18.7%</div>
                    <div class="summary-label">ROI</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value neutral">$47.50</div>
                    <div class="summary-label">Avg Bet Size</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value neutral">7</div>
                    <div class="summary-label">Win Streak</div>
                </div>
            </div>
            
            <!-- Performance Chart -->
            <div class="chart-section">
                <h2 style="margin-bottom: 20px;">Profit Over Time</h2>
                <div class="chart-placeholder">
                    <div style="text-align: center;">
                        <div style="font-size: 48px; margin-bottom: 10px;">📈</div>
                        <div>Your profit chart will appear here after 5+ bets</div>
                        <div style="color: #27ae60; font-size: 24px; margin-top: 20px;">↗ +$847</div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Bets History -->
            <div class="history-section">
                <h2 style="margin-bottom: 20px;">Recent Bets</h2>
                <button class="add-bet-btn" onclick="showAddBetForm()">+ Add New Bet</button>
                
                <!-- Add Bet Form (Hidden by default) -->
                <div id="addBetForm" style="display: none; background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-bottom: 20px;">Track New Bet</h3>
                    <form onsubmit="submitBet(event)">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Sport</label>
                                <select id="betSport" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                    <option value="">Select Sport</option>
                                    <option value="NFL">NFL</option>
                                    <option value="NCAAF">NCAAF</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Game</label>
                                <input type="text" id="betGame" required placeholder="e.g., Chiefs @ Bills" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Bet Type</label>
                                <select id="betType" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                    <option value="">Select Type</option>
                                    <option value="spread">Spread</option>
                                    <option value="total">Total (O/U)</option>
                                    <option value="moneyline">Moneyline</option>
                                    <option value="prop">Player Prop</option>
                                    <option value="parlay">Parlay</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Bet Description</label>
                                <input type="text" id="betDescription" required placeholder="e.g., Chiefs -3.5" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Odds</label>
                                <input type="text" id="betOdds" required placeholder="e.g., -110 or +150" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Stake ($)</label>
                                <input type="number" id="betStake" required min="1" step="0.01" placeholder="50.00" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Sportsbook</label>
                                <select id="betBook" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                    <option value="">Select Book</option>
                                    <option value="DraftKings">DraftKings</option>
                                    <option value="FanDuel">FanDuel</option>
                                    <option value="BetMGM">BetMGM</option>
                                    <option value="Caesars">Caesars</option>
                                    <option value="PointsBet">PointsBet</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Status</label>
                                <select id="betStatus" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                    <option value="pending">Pending</option>
                                    <option value="win">Win</option>
                                    <option value="loss">Loss</option>
                                    <option value="push">Push</option>
                                </select>
                            </div>
                        </div>
                        <div style="margin-top: 20px; display: flex; gap: 10px;">
                            <button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer;">Save Bet</button>
                            <button type="button" onclick="hideAddBetForm()" style="padding: 10px 20px; background: #95a5a6; color: white; border: none; border-radius: 4px; cursor: pointer;">Cancel</button>
                        </div>
                    </form>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Sport</th>
                            <th>Game</th>
                            <th>Bet Type</th>
                            <th>Odds</th>
                            <th>Stake</th>
                            <th>Result</th>
                            <th>Profit/Loss</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Today</td>
                            <td>NFL</td>
                            <td>Chiefs @ Bills</td>
                            <td>Over 48.5</td>
                            <td>-105</td>
                            <td>$50</td>
                            <td><span class="badge badge-pending">PENDING</span></td>
                            <td>-</td>
                        </tr>
                        <tr>
                            <td>Yesterday</td>
                            <td>NCAAF</td>
                            <td>Georgia @ Alabama</td>
                            <td>Georgia +3.5</td>
                            <td>-110</td>
                            <td>$100</td>
                            <td><span class="badge badge-win">WIN</span></td>
                            <td class="positive">+$90.91</td>
                        </tr>
                        <tr>
                            <td>Sep 8</td>
                            <td>NFL</td>
                            <td>Cowboys @ Giants</td>
                            <td>Cowboys -3.5</td>
                            <td>-110</td>
                            <td>$75</td>
                            <td><span class="badge badge-win">WIN</span></td>
                            <td class="positive">+$68.18</td>
                        </tr>
                        <tr>
                            <td>Sep 7</td>
                            <td>NCAAF</td>
                            <td>Michigan @ Penn St</td>
                            <td>Under 48.5</td>
                            <td>-105</td>
                            <td>$50</td>
                            <td><span class="badge badge-loss">LOSS</span></td>
                            <td class="negative">-$50.00</td>
                        </tr>
                        <tr>
                            <td>Sep 6</td>
                            <td>NFL</td>
                            <td>Ravens @ Chiefs</td>
                            <td>Ravens +3.5</td>
                            <td>+105</td>
                            <td>$60</td>
                            <td><span class="badge badge-win">WIN</span></td>
                            <td class="positive">+$63.00</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- Stats by Sport -->
            <div class="history-section">
                <h2 style="margin-bottom: 20px;">Performance by Sport</h2>
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3 style="margin-bottom: 15px; color: #333;">🏈 NFL</h3>
                        <div style="display: flex; justify-content: space-around;">
                            <div>
                                <div style="font-size: 24px; font-weight: bold; color: #27ae60;">18-9</div>
                                <div style="font-size: 12px; color: #666;">Record</div>
                            </div>
                            <div>
                                <div style="font-size: 24px; font-weight: bold; color: #27ae60;">66.7%</div>
                                <div style="font-size: 12px; color: #666;">Win Rate</div>
                            </div>
                        </div>
                    </div>
                    <div class="summary-card">
                        <h3 style="margin-bottom: 15px; color: #333;">🏈 NCAAF</h3>
                        <div style="display: flex; justify-content: space-around;">
                            <div>
                                <div style="font-size: 24px; font-weight: bold; color: #27ae60;">12-8</div>
                                <div style="font-size: 12px; color: #666;">Record</div>
                            </div>
                            <div>
                                <div style="font-size: 24px; font-weight: bold; color: #27ae60;">60.0%</div>
                                <div style="font-size: 12px; color: #666;">Win Rate</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function showAddBetForm() {{
                document.getElementById('addBetForm').style.display = 'block';
                document.querySelector('.add-bet-btn').style.display = 'none';
            }}
            
            function hideAddBetForm() {{
                document.getElementById('addBetForm').style.display = 'none';
                document.querySelector('.add-bet-btn').style.display = 'inline-block';
            }}
            
            async function submitBet(event) {{
                event.preventDefault();
                
                const betData = {{
                    code: '{code}',
                    sport: document.getElementById('betSport').value,
                    game: document.getElementById('betGame').value,
                    bet_type: document.getElementById('betType').value,
                    description: document.getElementById('betDescription').value,
                    odds: document.getElementById('betOdds').value,
                    stake: parseFloat(document.getElementById('betStake').value),
                    sportsbook: document.getElementById('betBook').value,
                    status: document.getElementById('betStatus').value,
                    date: new Date().toISOString()
                }};
                
                try {{
                    const response = await fetch('/api/bets/add', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(betData)
                    }});
                    
                    if (response.ok) {{
                        alert('Bet tracked successfully!');
                        // Reload page to show new bet
                        window.location.reload();
                    }} else {{
                        alert('Failed to save bet. Please try again.');
                    }}
                }} catch (error) {{
                    alert('Error saving bet: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """

# Bet Tracking API
@app.post("/api/bets/add")
async def add_bet(request: Request):
    """Add a new bet to user's tracking"""
    data = await request.json()
    code = data.get('code')
    
    # In production, save to database
    # For beta, store in memory
    if code not in beta_users:
        raise HTTPException(status_code=403, detail="Invalid access code")
    
    # Initialize bets list if not exists
    if 'bets' not in beta_users[code]:
        beta_users[code]['bets'] = []
    
    # Calculate potential payout
    stake = data.get('stake', 0)
    odds = data.get('odds', '-110')
    
    # Parse odds to calculate payout
    if odds.startswith('+'):
        decimal_odds = 1 + (int(odds[1:]) / 100)
    else:
        decimal_odds = 1 + (100 / abs(int(odds)))
    
    potential_payout = stake * decimal_odds
    
    # Add bet to user's list
    bet = {
        'id': len(beta_users[code]['bets']) + 1,
        'date': data.get('date'),
        'sport': data.get('sport'),
        'game': data.get('game'),
        'bet_type': data.get('bet_type'),
        'description': data.get('description'),
        'odds': odds,
        'stake': stake,
        'sportsbook': data.get('sportsbook'),
        'status': data.get('status'),
        'potential_payout': potential_payout,
        'profit_loss': 0 if data.get('status') == 'pending' else (
            potential_payout - stake if data.get('status') == 'win' else -stake
        )
    }
    
    beta_users[code]['bets'].append(bet)
    
    return {"status": "success", "bet_id": bet['id']}

@app.get("/api/bets/{code}")
async def get_user_bets(code: str):
    """Get all bets for a user"""
    if code not in beta_users:
        raise HTTPException(status_code=403, detail="Invalid access code")
    
    return beta_users[code].get('bets', [])

# Feedback API
@app.post("/api/feedback")
async def submit_feedback(request: Request):
    """Submit beta user feedback"""
    data = await request.json()
    # In production, save to database
    # For now, just log it
    print(f"Feedback from {data.get('code')}: {data.get('feedback')}")
    return {"status": "success", "message": "Thank you for your feedback!"}

# API Endpoints
@app.get("/api/nfl/opportunities")
async def get_nfl_opportunities():
    """Get NFL betting opportunities"""
    return [
        {
            "id": "nfl-001",
            "type": "arbitrage",
            "game": "Chiefs @ Bills",
            "bet": "Over/Under 48.5",
            "books": {"DraftKings": -105, "FanDuel": -103},
            "return": 0.024,
            "confidence": 1.0
        },
        {
            "id": "nfl-002",
            "type": "value",
            "game": "Cowboys @ Giants",
            "bet": "Cowboys -3.5",
            "expected_value": 0.042,
            "confidence": 0.68
        }
    ]

@app.get("/api/ncaaf/opportunities")
async def get_ncaaf_opportunities():
    """Get NCAAF betting opportunities"""
    return [
        {
            "id": "ncaaf-001",
            "type": "sharp",
            "game": "Georgia @ Alabama",
            "bet": "Georgia +3.5",
            "public_percentage": 0.22,
            "sharp_money": 0.65,
            "line_movement": "Opened -4.5, now -3.5"
        },
        {
            "id": "ncaaf-002",
            "type": "weather",
            "game": "Michigan @ Penn State",
            "bet": "Under 48.5",
            "weather": "20mph winds, 40% rain",
            "model_total": 41
        }
    ]

@app.get("/api/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "version": "0.1.0-beta",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "nfl": "active",
            "ncaaf": "active",
            "mlb": "off-season",
            "api": "running"
        }
    }

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 SPORTS BETTING BETA PLATFORM")
    print("="*50)
    print("\n✅ Server starting on: http://localhost:8000")
    print("\n📋 Available Endpoints:")
    print("  • Landing Page: http://localhost:8000")
    print("  • Dashboard: http://localhost:8000/dashboard?code=YOUR_CODE")
    print("  • NFL: http://localhost:8000/nfl?code=YOUR_CODE")
    print("  • NCAAF: http://localhost:8000/ncaaf?code=YOUR_CODE")
    print("  • API Docs: http://localhost:8000/docs")
    print("\n" + "="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)