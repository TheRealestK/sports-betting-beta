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

# Add path for model imports
sys.path.append('/Users/therealestk/sports betting 100')

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
    
    # Load NFL models
    try:
        nfl_path = "/Users/therealestk/sports betting 100/nfl_trained_models"
        if os.path.exists(f"{nfl_path}/spread_xgb.pkl"):
            with open(f"{nfl_path}/spread_xgb.pkl", "rb") as f:
                ML_MODELS["nfl"]["spread"] = pickle.load(f)
            with open(f"{nfl_path}/total_xgb.pkl", "rb") as f:
                ML_MODELS["nfl"]["total"] = pickle.load(f)
            with open(f"{nfl_path}/scalers.pkl", "rb") as f:
                ML_MODELS["nfl"]["scaler"] = pickle.load(f)
            
            # Import the adapter
            from nfl_feature_adapter import NFLFeatureAdapter
            ML_MODELS["nfl"]["adapter"] = NFLFeatureAdapter()
            print("✅ NFL models loaded")
    except Exception as e:
        print(f"❌ NFL models failed: {e}")
    
    # Load MLB models
    try:
        mlb_path = "/Users/therealestk/sports betting 100/models/mlb_models.pkl"
        if os.path.exists(mlb_path):
            with open(mlb_path, "rb") as f:
                ML_MODELS["mlb"]["models"] = pickle.load(f)
            print("✅ MLB models loaded")
    except Exception as e:
        print(f"❌ MLB models failed: {e}")

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
    """Sport dashboard with ML predictions."""
    cache = SERVER_CACHE.get(sport, {})
    games = cache.get("data", [])
    predictions = cache.get("predictions", {})
    
    if not games:
        return HTMLResponse(f"<h1>No {sport.upper()} games available. Refresh in a moment.</h1>")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{sport.upper()} Dashboard - ML Enhanced</title>
        <style>
            body {{ font-family: sans-serif; background: #1a1a2e; color: white; padding: 20px; }}
            .header {{ background: #0f3460; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .game-card {{ background: #16213e; padding: 20px; margin: 15px 0; border-radius: 10px; }}
            .ml-prediction {{ background: #2ecc71; color: black; padding: 10px; margin: 10px 0; border-radius: 5px; }}
            .edge-alert {{ background: #e74c3c; color: white; padding: 5px 10px; border-radius: 5px; }}
            .odds-box {{ background: #34495e; padding: 10px; margin: 5px 0; border-radius: 5px; }}
            .confidence {{ display: inline-block; padding: 5px 10px; border-radius: 5px; }}
            .high-conf {{ background: #27ae60; }}
            .med-conf {{ background: #f39c12; }}
            .low-conf {{ background: #7f8c8d; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏆 {sport.upper()} Betting Dashboard</h1>
            <p>📅 Last Updated: {cache.get('last_updated').strftime('%I:%M %p') if cache.get('last_updated') else 'Loading...'}</p>
            <p>🎮 Games: {len(games)} | 🤖 ML Predictions: {len(predictions)}</p>
        </div>
    """
    
    for game in games[:15]:  # Show first 15 games
        game_id = game.get("id", "")
        pred = predictions.get(game_id, {})
        
        html += f"""
        <div class="game-card">
            <h3>🏟️ {game['home_team']} vs {game['away_team']}</h3>
            <p>🕐 {game.get('commence_time', 'TBD')[:10]}</p>
        """
        
        # Show current odds
        if game.get('bookmakers'):
            book = game['bookmakers'][0]
            html += f"<div class='odds-box'>📖 {book['title']} Odds:<br>"
            
            for market in book.get('markets', [])[:2]:
                if market['key'] == 'spreads':
                    html += f"Spread: {market['outcomes'][0].get('point', 'N/A')}<br>"
                elif market['key'] == 'totals':
                    html += f"Total: {market['outcomes'][0].get('point', 'N/A')}<br>"
            html += "</div>"
        
        # Show ML predictions if available
        if pred and pred.get("spread") is not None:
            conf_class = "high-conf" if pred["confidence"] > 75 else "med-conf" if pred["confidence"] > 60 else "low-conf"
            
            html += f"""
            <div class="ml-prediction">
                <strong>🤖 ML Predictions:</strong><br>
                Spread: {pred['spread']} (Market: {pred.get('market_spread', 'N/A')})<br>
                Total: {pred['total']} (Market: {pred.get('market_total', 'N/A')})<br>
                <span class="confidence {conf_class}">Confidence: {pred['confidence']:.0f}%</span>
                """
            
            if pred.get("ml_edge"):
                html += f""" <span class="edge-alert">⚡ EDGE DETECTED</span>"""
            
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
    
    uvicorn.run(app, host="0.0.0.0", port=8010)