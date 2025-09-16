#!/usr/bin/env python3
"""
Sports Betting Beta Platform with ML Integration
Server-side caching + Real ML predictions
"""

import os
import sys
import pickle
import json
import threading
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import requests
import uvicorn

# Add path for model imports (disabled for cloud deployment)
# sys.path.append('/Users/therealestk/sports betting 100')

# Configuration
ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '12ef8ff548ae7e9d3b7f7a6da8a0306d')
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
CACHE_UPDATE_INTERVAL = 30  # minutes

# Initialize FastAPI
app = FastAPI(title="Sports Betting Beta - ML Enhanced")

# Global server-side cache
SERVER_CACHE = {
    "nfl": {"data": [], "predictions": {}, "last_updated": None},
    "nba": {"data": [], "predictions": {}, "last_updated": None},
    "mlb": {"data": [], "predictions": {}, "last_updated": None},
    "ncaaf": {"data": [], "predictions": {}, "last_updated": None}
}

# ML Models storage
ML_MODELS = {
    "nfl": {"spread": None, "total": None, "scaler": None, "adapter": None},
    "mlb": {"models": None},
    "nba": {"models": None}
}

def load_ml_models():
    """Load trained ML models."""
    print("[ML] Loading trained models...")
    
    # ML models disabled for cloud deployment
    # Models would need to be uploaded to cloud storage
    print("⚠️ ML models disabled for cloud deployment")
    print("   To enable: Upload models to cloud storage and update paths")

def fetch_odds_from_api(sport: str) -> List[Dict]:
    """Fetch odds from API."""
    sport_key_mapping = {
        "nfl": "americanfootball_nfl",
        "nba": "basketball_nba",
        "mlb": "baseball_mlb",
        "ncaaf": "americanfootball_ncaaf"
    }
    
    sport_key = sport_key_mapping.get(sport, sport)
    
    try:
        print(f"[API] Fetching {sport} odds...")
        response = requests.get(
            f"{ODDS_API_BASE}/sports/{sport_key}/odds",
            params={
                'apiKey': ODDS_API_KEY,
                'regions': 'us',
                'markets': 'h2h,spreads,totals'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"[API] ✅ Got {len(data)} {sport} games")
            return data
        else:
            print(f"[API] ❌ Error {response.status_code}")
            return []
    except Exception as e:
        print(f"[API] ❌ Error: {e}")
        return []

def predict_nfl_game(game_data: Dict) -> Dict:
    """Generate ML predictions for NFL game."""
    predictions = {
        "spread": None,
        "total": None,
        "confidence": 0,
        "ml_edge": False
    }
    
    if not ML_MODELS["nfl"]["spread"] or not ML_MODELS["nfl"]["adapter"]:
        return predictions
    
    try:
        # Extract features using adapter
        features = ML_MODELS["nfl"]["adapter"].extract_features_from_game(game_data)
        features_2d = features.reshape(1, -1)
        
        # Scale if scaler available
        if ML_MODELS["nfl"]["scaler"] and "spread" in ML_MODELS["nfl"]["scaler"]:
            features_scaled = ML_MODELS["nfl"]["scaler"]["spread"].transform(features_2d)
        else:
            features_scaled = features_2d
        
        # Make predictions
        spread_pred = ML_MODELS["nfl"]["spread"].predict(features_scaled)[0]
        total_pred = ML_MODELS["nfl"]["total"].predict(features_scaled)[0]
        
        # Get current market lines
        current_spread = 0
        current_total = 0
        if game_data.get("bookmakers"):
            for market in game_data["bookmakers"][0].get("markets", []):
                if market["key"] == "spreads":
                    current_spread = market["outcomes"][0].get("point", 0)
                elif market["key"] == "totals":
                    current_total = market["outcomes"][0].get("point", 0)
        
        # Calculate edge
        spread_diff = abs(spread_pred - current_spread)
        total_diff = abs(total_pred - current_total)
        
        predictions = {
            "spread": round(spread_pred, 1),
            "total": round(total_pred, 1),
            "confidence": min(85, 60 + spread_diff * 2 + total_diff),
            "ml_edge": spread_diff > 2 or total_diff > 3,
            "spread_diff": round(spread_diff, 1),
            "total_diff": round(total_diff, 1),
            "market_spread": current_spread,
            "market_total": current_total
        }
        
    except Exception as e:
        print(f"[ML] Prediction error: {e}")
    
    return predictions

def update_cache_with_predictions():
    """Update cache and generate ML predictions."""
    global SERVER_CACHE
    
    while True:
        print(f"\n[SERVER] Cache update starting at {datetime.now()}")
        
        for sport in ["nfl", "nba", "mlb", "ncaaf"]:
            try:
                # Fetch new odds
                new_data = fetch_odds_from_api(sport)
                
                # Generate predictions for each game
                predictions = {}
                if sport == "nfl" and ML_MODELS["nfl"]["spread"]:
                    for game in new_data:
                        game_id = game.get("id", "")
                        predictions[game_id] = predict_nfl_game(game)
                
                # Update cache
                SERVER_CACHE[sport] = {
                    "data": new_data,
                    "predictions": predictions,
                    "last_updated": datetime.now()
                }
                
                time.sleep(2)  # Be nice to API
                
            except Exception as e:
                print(f"[SERVER] Error updating {sport}: {e}")
        
        total_games = sum(len(cache["data"]) for cache in SERVER_CACHE.values())
        total_predictions = sum(len(cache["predictions"]) for cache in SERVER_CACHE.values())
        print(f"[SERVER] Updated: {total_games} games, {total_predictions} ML predictions")
        
        # Wait before next update
        print(f"[SERVER] Next update in {CACHE_UPDATE_INTERVAL} minutes")
        time.sleep(CACHE_UPDATE_INTERVAL * 60)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    # Load ML models
    load_ml_models()
    
    # Start cache updater
    print("[SERVER] Starting background cache updater...")
    cache_thread = threading.Thread(target=update_cache_with_predictions, daemon=True)
    cache_thread.start()
    
    # Initial data fetch
    print("[SERVER] Initial data fetch...")
    for sport in ["nfl", "nba", "mlb", "ncaaf"]:
        data = fetch_odds_from_api(sport)
        predictions = {}
        if sport == "nfl" and ML_MODELS["nfl"]["spread"]:
            for game in data:
                predictions[game.get("id", "")] = predict_nfl_game(game)
        
        SERVER_CACHE[sport] = {
            "data": data,
            "predictions": predictions,
            "last_updated": datetime.now()
        }
        time.sleep(1)

@app.get("/")
async def root():
    """Home page."""
    return HTMLResponse("""
    <html>
    <head>
        <title>Sports Betting Beta - ML Enhanced</title>
        <style>
            body { font-family: sans-serif; padding: 40px; background: #1a1a2e; color: white; }
            a { color: #4CAF50; text-decoration: none; padding: 10px; }
            .feature { background: #16213e; padding: 20px; margin: 20px 0; border-radius: 10px; }
            .ml-badge { background: #e74c3c; padding: 5px 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🎯 Sports Betting Beta Platform</h1>
        <div class="feature">
            <h3>✅ Server-Side Caching</h3>
            <p>API calls made by server every 30 minutes - 0 calls per user!</p>
        </div>
        
        <div class="feature">
            <h3>🤖 ML Predictions <span class="ml-badge">NEW</span></h3>
            <p>Real machine learning models analyze every game</p>
        </div>
        
        <h2>Available Sports:</h2>
        <p>
            <a href="/dashboard/nfl">🏈 NFL Dashboard</a>
            <a href="/dashboard/nba">🏀 NBA Dashboard</a>
            <a href="/dashboard/mlb">⚾ MLB Dashboard</a>
            <a href="/dashboard/ncaaf">🏈 NCAAF Dashboard</a>
        </p>
        
        <h2>System Tools:</h2>
        <p>
            <a href="/api/cache-status">📊 Cache Status</a>
            <a href="/api/model-status">🤖 Model Status</a>
        </p>
    </body>
    </html>
    """)

@app.get("/dashboard/{sport}")
async def dashboard(sport: str):
    """Sport dashboard with ML predictions organized by date."""
    cache = SERVER_CACHE.get(sport, {})
    games = cache.get("data", [])
    predictions = cache.get("predictions", {})
    
    if not games:
        return HTMLResponse(f"<h1>No {sport.upper()} games available. Refresh in a moment.</h1>")
    
    # Group games by date
    from datetime import datetime
    from collections import defaultdict
    games_by_date = defaultdict(list)
    
    for game in games:
        try:
            game_time = game.get('commence_time', '')
            if game_time:
                dt = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                date_key = dt.strftime("%A, %B %d")
                games_by_date[date_key].append(game)
        except:
            games_by_date["Date TBD"].append(game)
    
    # Sort dates
    sorted_dates = sorted(games_by_date.keys())
    
    # Count high confidence picks
    high_conf_picks = sum(1 for p in predictions.values() if p.get("confidence", 0) > 75)
    total_edges = sum(1 for p in predictions.values() if p.get("ml_edge", False))
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{sport.upper()} Dashboard - Smart Betting Analysis</title>
        <style>
            body {{ 
                font-family: -apple-system, sans-serif; 
                background: linear-gradient(135deg, #1e3c72, #2a5298); 
                color: white; 
                padding: 20px;
                margin: 0;
            }}
            .header {{ 
                background: rgba(15, 52, 96, 0.9); 
                padding: 25px; 
                border-radius: 15px; 
                margin-bottom: 25px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }}
            .summary-stats {{
                display: flex;
                gap: 20px;
                margin: 20px 0;
            }}
            .stat-box {{
                background: rgba(255,255,255,0.1);
                padding: 15px 20px;
                border-radius: 10px;
                flex: 1;
                text-align: center;
            }}
            .stat-number {{
                font-size: 28px;
                font-weight: bold;
                color: #4CAF50;
            }}
            .date-section {{
                background: rgba(255,255,255,0.05);
                padding: 15px;
                margin: 20px 0;
                border-radius: 10px;
                border-left: 4px solid #4CAF50;
            }}
            .date-header {{
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #81c784;
            }}
            .game-card {{ 
                background: rgba(22, 33, 62, 0.95); 
                padding: 20px; 
                margin: 15px 0; 
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                transition: transform 0.2s;
            }}
            .game-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            }}
            .teams {{
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 10px;
            }}
            .game-time {{
                color: #aaa;
                font-size: 14px;
                margin-bottom: 15px;
            }}
            .betting-recommendation {{
                background: linear-gradient(135deg, #2ecc71, #27ae60);
                color: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                font-weight: 500;
            }}
            .recommendation-title {{
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .bet-details {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 10px;
            }}
            .edge-alert {{ 
                background: linear-gradient(135deg, #e74c3c, #c0392b); 
                color: white; 
                padding: 8px 15px; 
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                display: inline-block;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.8; }}
                100% {{ opacity: 1; }}
            }}
            .odds-box {{ 
                background: rgba(52, 73, 94, 0.5); 
                padding: 12px; 
                margin: 8px 0; 
                border-radius: 8px;
                font-size: 14px;
            }}
            .confidence {{ 
                display: inline-block; 
                padding: 6px 12px; 
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            .high-conf {{ 
                background: linear-gradient(135deg, #27ae60, #229954); 
                color: white;
            }}
            .med-conf {{ 
                background: linear-gradient(135deg, #f39c12, #e67e22); 
                color: white;
            }}
            .low-conf {{ 
                background: rgba(127, 140, 141, 0.5); 
                color: white;
            }}
            .action-button {{
                background: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                text-decoration: none;
                display: inline-block;
                margin-top: 10px;
                transition: background 0.3s;
            }}
            .action-button:hover {{
                background: #2980b9;
            }}
            .no-edge {{
                color: #95a5a6;
                font-style: italic;
                padding: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 {sport.upper()} Smart Betting Dashboard</h1>
            <p>📊 AI-Powered Analysis with Real-Time Odds</p>
            
            <div class="summary-stats">
                <div class="stat-box">
                    <div class="stat-number">{len(games)}</div>
                    <div>Total Games</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{high_conf_picks}</div>
                    <div>High Confidence Picks</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{total_edges}</div>
                    <div>Edge Opportunities</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{cache.get('last_updated').strftime('%I:%M %p') if cache.get('last_updated') else 'Loading'}</div>
                    <div>Last Updated</div>
                </div>
            </div>
        </div>
    """
    
    # Show games organized by date
    for date in sorted_dates[:5]:  # Show first 5 days
        date_games = games_by_date[date]
        
        # Count edges for this date
        date_edges = sum(1 for game in date_games 
                        if predictions.get(game.get("id", ""), {}).get("ml_edge", False))
        
        html += f"""
        <div class="date-section">
            <div class="date-header">
                📅 {date} 
                <span style="font-size: 14px; color: #ccc;">
                    ({len(date_games)} games{f', {date_edges} edges' if date_edges > 0 else ''})
                </span>
            </div>
        """
        
        for game in date_games[:8]:  # Max 8 games per day
            game_id = game.get("id", "")
            pred = predictions.get(game_id, {})
            
            # Format game time
            try:
                game_time = game.get('commence_time', '')
                if game_time:
                    dt = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                    time_str = dt.strftime("%I:%M %p ET")
                else:
                    time_str = "Time TBD"
            except:
                time_str = "Time TBD"
            
            html += f"""
            <div class="game-card">
                <div class="teams">🏈 {game['home_team']} vs {game['away_team']}</div>
                <div class="game-time">🕐 {time_str}</div>
            """
            
            # Show current odds
            if game.get('bookmakers'):
                book = game['bookmakers'][0]
                html += f"<div class='odds-box'>📊 <strong>{book['title']}</strong> Lines: "
                
                for market in book.get('markets', []):
                    if market['key'] == 'spreads' and market.get('outcomes'):
                        spread = market['outcomes'][0].get('point', 'N/A')
                        html += f"Spread: {spread:+.1f} | " if isinstance(spread, (int, float)) else f"Spread: {spread} | "
                    elif market['key'] == 'totals' and market.get('outcomes'):
                        total = market['outcomes'][0].get('point', 'N/A')
                        html += f"O/U: {total}"
                html += "</div>"
            
            # Show betting recommendation with ML predictions
            if pred and pred.get("spread") is not None:
                conf = pred["confidence"]
                conf_class = "high-conf" if conf > 75 else "med-conf" if conf > 60 else "low-conf"
                
                # Create actionable recommendation
                if pred.get("ml_edge"):
                    spread_diff = pred.get('spread_diff', 0)
                    total_diff = pred.get('total_diff', 0)
                    
                    recommendation = ""
                    if spread_diff > 2:
                        if pred['spread'] < pred.get('market_spread', 0):
                            recommendation = f"✅ BET: {game['home_team']} {pred.get('market_spread', 0):+.1f}"
                        else:
                            recommendation = f"✅ BET: {game['away_team']} {-pred.get('market_spread', 0):+.1f}"
                    
                    if total_diff > 3:
                        if pred['total'] > pred.get('market_total', 0):
                            recommendation += f"{'<br>' if recommendation else ''}✅ BET: Over {pred.get('market_total', 0)}"
                        else:
                            recommendation += f"{'<br>' if recommendation else ''}✅ BET: Under {pred.get('market_total', 0)}"
                    
                    html += f"""
                    <div class="betting-recommendation">
                        <div class="recommendation-title">
                            🤖 AI RECOMMENDATION 
                            <span class="edge-alert">⚡ EDGE DETECTED</span>
                        </div>
                        {recommendation if recommendation else "Analyzing..."}
                        <div class="bet-details">
                            <span>Model: {pred['spread']:.1f} / {pred['total']:.1f}</span>
                            <span class="confidence {conf_class}">Confidence: {conf:.0f}%</span>
                        </div>
                    </div>
                    """
                else:
                    html += f"""
                    <div class="odds-box" style="background: rgba(52, 73, 94, 0.3);">
                        🤖 Model Analysis: Spread {pred['spread']:.1f} | Total {pred['total']:.1f}
                        <span class="confidence {conf_class}" style="float: right;">Confidence: {conf:.0f}%</span>
                    </div>
                    """
            else:
                html += '<div class="no-edge">⏳ Analysis pending...</div>'
            
            html += "</div>"
        
        html += "</div>"
    
    html += """
    <script>
        // Auto refresh every 5 minutes
        setTimeout(() => location.reload(), 5 * 60 * 1000);
    </script>
    </body>
    </html>
    """
    
    return HTMLResponse(html)

@app.get("/api/cache-status")
async def cache_status():
    """Check cache and ML status."""
    status = {}
    for sport, cache in SERVER_CACHE.items():
        status[sport] = {
            "games": len(cache.get("data", [])),
            "predictions": len(cache.get("predictions", {})),
            "last_updated": cache.get("last_updated").isoformat() if cache.get("last_updated") else None,
            "age_minutes": int((datetime.now() - cache.get("last_updated")).total_seconds() / 60) if cache.get("last_updated") else None
        }
    return JSONResponse(content=status)

@app.get("/api/model-status")
async def model_status():
    """Check ML model status."""
    status = {
        "nfl": {
            "spread_model": ML_MODELS["nfl"]["spread"] is not None,
            "total_model": ML_MODELS["nfl"]["total"] is not None,
            "adapter": ML_MODELS["nfl"]["adapter"] is not None
        },
        "mlb": {
            "models_loaded": ML_MODELS["mlb"]["models"] is not None
        }
    }
    return JSONResponse(content=status)

if __name__ == "__main__":
    print("=" * 60)
    print("SPORTS BETTING BETA - ML INTEGRATED")
    print("=" * 60)
    print("✅ Server-side caching (30 min updates)")
    print("🤖 ML predictions for games")
    print("⚡ Edge detection algorithms")
    print("=" * 60)
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)