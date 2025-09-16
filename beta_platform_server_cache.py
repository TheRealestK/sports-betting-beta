#!/usr/bin/env python3
"""
Enhanced Beta Platform with Server-Side Data Fetching
API calls are made automatically by the server, not per user request
"""

import os
import sys
import json
import hashlib
import secrets
import asyncio
import requests
import numpy as np
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from fastapi import FastAPI, Request, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import uvicorn

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
GOOGLE_ANALYTICS_ID = "G-FPHYK266CT"
ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '12ef8ff548ae7e9d3b7f7a6da8a0306d')
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Initialize FastAPI
app = FastAPI(title="Sports Betting Beta - Server Cached")

# Global server-side cache
SERVER_ODDS_CACHE = {
    "nfl": {"data": [], "last_updated": None},
    "nba": {"data": [], "last_updated": None},
    "mlb": {"data": [], "last_updated": None},
    "ncaaf": {"data": [], "last_updated": None}
}

# Cache update interval (in minutes)
CACHE_UPDATE_INTERVAL = 30  # Update every 30 minutes

def fetch_odds_from_api(sport: str) -> List[Dict]:
    """Fetch odds from API - called by server, not users"""
    sport_key_mapping = {
        "nfl": "americanfootball_nfl",
        "nba": "basketball_nba",
        "mlb": "baseball_mlb",
        "ncaaf": "americanfootball_ncaaf"
    }
    
    sport_key = sport_key_mapping.get(sport, sport)
    
    try:
        print(f"[SERVER] Fetching {sport} odds at {datetime.now()}")
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
            print(f"[SERVER] ✅ Got {len(data)} {sport} games")
            print(f"[SERVER] API calls remaining: {response.headers.get('x-requests-remaining', 'N/A')}")
            return data
        else:
            print(f"[SERVER] ❌ API error {response.status_code}")
            return []
    except Exception as e:
        print(f"[SERVER] ❌ Error fetching {sport}: {e}")
        return []

def update_server_cache():
    """Update the server cache - runs in background thread"""
    global SERVER_ODDS_CACHE
    
    while True:
        print(f"\n[SERVER] Starting cache update at {datetime.now()}")
        
        for sport in ["nfl", "nba", "mlb", "ncaaf"]:
            try:
                # Fetch new data
                new_data = fetch_odds_from_api(sport)
                
                # Update cache
                SERVER_ODDS_CACHE[sport] = {
                    "data": new_data,
                    "last_updated": datetime.now()
                }
                
                # Small delay between sports to be nice to API
                time.sleep(2)
                
            except Exception as e:
                print(f"[SERVER] Error updating {sport}: {e}")
        
        # Calculate total games
        total_games = sum(len(cache["data"]) for cache in SERVER_ODDS_CACHE.values())
        print(f"[SERVER] Cache updated: {total_games} total games across all sports")
        
        # Wait before next update
        print(f"[SERVER] Next update in {CACHE_UPDATE_INTERVAL} minutes")
        time.sleep(CACHE_UPDATE_INTERVAL * 60)

# Start background cache updater when server starts
@app.on_event("startup")
async def startup_event():
    """Start the background cache updater"""
    print("[SERVER] Starting background cache updater...")
    cache_thread = threading.Thread(target=update_server_cache, daemon=True)
    cache_thread.start()
    
    # Do initial fetch immediately
    print("[SERVER] Performing initial data fetch...")
    for sport in ["nfl", "nba", "mlb", "ncaaf"]:
        data = fetch_odds_from_api(sport)
        SERVER_ODDS_CACHE[sport] = {
            "data": data,
            "last_updated": datetime.now()
        }
        time.sleep(1)

def get_cached_odds(sport: str) -> List[Dict]:
    """Get odds from SERVER cache - no API calls made here"""
    sport_map = {
        "americanfootball_nfl": "nfl",
        "basketball_nba": "nba", 
        "baseball_mlb": "mlb",
        "americanfootball_ncaaf": "ncaaf"
    }
    
    cache_key = sport_map.get(sport, sport)
    cache = SERVER_ODDS_CACHE.get(cache_key, {})
    
    # Return cached data (users NEVER trigger API calls)
    return cache.get("data", [])

@app.get("/api/cache-status")
async def cache_status():
    """Endpoint to check cache status"""
    status = {}
    for sport, cache in SERVER_ODDS_CACHE.items():
        status[sport] = {
            "games": len(cache.get("data", [])),
            "last_updated": cache.get("last_updated").isoformat() if cache.get("last_updated") else None,
            "age_minutes": int((datetime.now() - cache.get("last_updated")).total_seconds() / 60) if cache.get("last_updated") else None
        }
    return JSONResponse(content=status)

# Storage (same as before)
users_db = {}
sessions = {}
user_performance = {}
bet_history = []

def format_game_time(iso_time: str) -> str:
    """Format ISO time to readable format"""
    try:
        if iso_time:
            dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            return dt.strftime("%b %d, %I:%M %p ET")
        return "Time TBD"
    except:
        return "Time TBD"

class BettingRecommendation:
    """Generate clear betting recommendations"""
    
    @staticmethod
    def generate_recommendation(game_data: Dict, analysis: Dict) -> Dict:
        """Create a clear betting recommendation"""
        
        recommendation = {
            "game_id": game_data.get("id"),
            "teams": f"{game_data['home_team']} vs {game_data['away_team']}",
            "bets": []
        }
        
        # Extract current odds
        if game_data.get("bookmakers"):
            bookmaker = game_data["bookmakers"][0]
            for market in bookmaker.get("markets", []):
                if market["key"] == "spreads":
                    spread = market["outcomes"][0].get("point", 0)
                    spread_odds = market["outcomes"][0].get("price", 1.91)
                elif market["key"] == "totals":
                    total = market["outcomes"][0].get("point", 0)
                    total_odds = market["outcomes"][0].get("price", 1.91)
                elif market["key"] == "h2h":
                    home_ml = next((o["price"] for o in market["outcomes"] 
                                   if o["name"] == game_data["home_team"]), 2.0)
                    away_ml = next((o["price"] for o in market["outcomes"] 
                                   if o["name"] == game_data["away_team"]), 2.0)
        
        confidence = analysis.get("confidence_score", 50)
        
        # Generate recommendations based on confidence
        if confidence >= 75:
            if analysis.get("favorite") == "home":
                recommendation["bets"].append({
                    "type": "SPREAD",
                    "pick": f"{game_data['home_team']} {spread:+.1f}",
                    "odds": spread_odds,
                    "confidence": confidence,
                    "reason": f"Strong edge on home favorite",
                    "suggested_unit": 2.0,
                    "priority": 1
                })
        
        return recommendation

def analyze_game_with_ml(game_data: Dict, sport: str) -> Dict:
    """Analyze game - simplified version"""
    analysis = {
        "confidence_score": np.random.uniform(55, 85),
        "confidence_level": "GOOD",
        "favorite": "home" if np.random.random() > 0.5 else "away",
        "edge": np.random.uniform(2, 10),
        "ml_confidence": np.random.uniform(60, 90)
    }
    
    if analysis["confidence_score"] >= 80:
        analysis["confidence_level"] = "ELITE"
    elif analysis["confidence_score"] >= 70:
        analysis["confidence_level"] = "HIGH"
    elif analysis["confidence_score"] >= 60:
        analysis["confidence_level"] = "GOOD"
    else:
        analysis["confidence_level"] = "FAIR"
    
    return analysis

@app.get("/dashboard/{sport}")
async def dashboard(sport: str = "nfl", user: str = None):
    """Dashboard showing real odds from server cache"""
    
    # Get data from SERVER CACHE (no API call)
    games = get_cached_odds(f"americanfootball_{sport}" if sport in ["nfl", "ncaaf"] else f"basketball_{sport}" if sport == "nba" else f"baseball_{sport}")
    
    if not games:
        cache_info = SERVER_ODDS_CACHE.get(sport, {})
        last_update = cache_info.get("last_updated", "Never")
        return HTMLResponse(f"""
        <html>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>No {sport.upper()} Games Available</h1>
            <p>The server is fetching data. Please refresh in a moment.</p>
            <p>Last update attempt: {last_update}</p>
            <p><a href="/api/cache-status">Check Cache Status</a></p>
            <button onclick="location.reload()">Refresh Page</button>
        </body>
        </html>
        """)
    
    # Generate dashboard HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sports Betting - {sport.upper()} (Server Cached)</title>
        <style>
            body {{ font-family: sans-serif; background: #1e3c72; color: white; padding: 20px; }}
            .header {{ background: white; color: black; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .cache-info {{ background: #4CAF50; padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .game-card {{ background: white; color: black; padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .bet-recommendation {{ background: #2196F3; color: white; padding: 10px; margin: 5px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{sport.upper()} Betting Analysis</h1>
            <div class="cache-info">
                📊 Server Cache: {len(games)} games loaded<br>
                🔄 Auto-updates every {CACHE_UPDATE_INTERVAL} minutes<br>
                ⚡ No API calls per user - all data served from cache!<br>
                Last updated: {SERVER_ODDS_CACHE[sport]['last_updated'].strftime('%I:%M %p') if SERVER_ODDS_CACHE[sport].get('last_updated') else 'Loading...'}
            </div>
        </div>
    """
    
    # Show games
    for game in games[:10]:  # Show first 10 games
        html_content += f"""
        <div class="game-card">
            <h3>{game['home_team']} vs {game['away_team']}</h3>
            <p>🕐 {format_game_time(game.get('commence_time', ''))}</p>
        """
        
        # Show odds from first bookmaker
        if game.get('bookmakers'):
            book = game['bookmakers'][0]
            html_content += f"<p>📖 {book['title']} Odds:</p><ul>"
            
            for market in book.get('markets', [])[:2]:
                html_content += f"<li>{market['key']}: "
                for outcome in market.get('outcomes', [])[:2]:
                    html_content += f"{outcome.get('name')}: {outcome.get('price')} "
                html_content += "</li>"
            html_content += "</ul>"
        
        html_content += "</div>"
    
    html_content += """
    <script>
        // Auto refresh every 5 minutes
        setTimeout(() => location.reload(), 5 * 60 * 1000);
    </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/")
async def root():
    """Home page"""
    return HTMLResponse("""
    <html>
    <body style="font-family: sans-serif; padding: 40px;">
        <h1>Sports Betting Beta - Server Cached Version</h1>
        <p>This version uses server-side caching. API calls are made automatically by the server, not per user!</p>
        
        <h2>Available Sports:</h2>
        <ul>
            <li><a href="/dashboard/nfl">NFL Dashboard</a></li>
            <li><a href="/dashboard/nba">NBA Dashboard</a></li>
            <li><a href="/dashboard/mlb">MLB Dashboard</a></li>
            <li><a href="/dashboard/ncaaf">NCAAF Dashboard</a></li>
        </ul>
        
        <h2>System Status:</h2>
        <ul>
            <li><a href="/api/cache-status">Cache Status</a> - See when data was last updated</li>
        </ul>
        
        <div style="margin-top: 30px; padding: 20px; background: #f0f0f0; border-radius: 10px;">
            <h3>How it works:</h3>
            <p>✅ Server fetches odds every 30 minutes automatically</p>
            <p>✅ All users see the same cached data</p>
            <p>✅ 0 API calls per user visit</p>
            <p>✅ Can handle unlimited users with same API usage</p>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    print("=" * 60)
    print("SPORTS BETTING BETA - SERVER CACHED VERSION")
    print("=" * 60)
    print(f"API calls are made by the SERVER every {CACHE_UPDATE_INTERVAL} minutes")
    print("Users DO NOT trigger API calls - they only see cached data")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)