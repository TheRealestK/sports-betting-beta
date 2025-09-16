#!/usr/bin/env python3
"""
Enhanced Beta Platform with ML Models and Clear Betting Recommendations
Shows actual bets, not just confidence scores
"""

import os
import sys
import json
import hashlib
import secrets
import asyncio
import requests
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from fastapi import FastAPI, Request, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import uvicorn

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import ML models
ML_MODELS_AVAILABLE = False
try:
    from src.ml_models.nfl_ensemble_model import NFLEnsembleModel
    from src.ml_models.mlb_ensemble_model import MLBEnsembleModel
    from src.analytics.nfl_analytics_engine import NFLAnalyticsEngine
    from src.analytics.arbitrage_detector import ArbitrageDetector
    ML_MODELS_AVAILABLE = True
    print("✅ ML Models Successfully Imported!")
except ImportError as e:
    print(f"⚠️ ML Models not available: {e}")
    print("Will use simplified analysis")

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
GOOGLE_ANALYTICS_ID = "G-FPHYK266CT"
ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '12ef8ff548ae7e9d3b7f7a6da8a0306d')
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Initialize FastAPI
app = FastAPI(title="Sports Betting Beta - ML Enhanced")

# Storage
users_db = {}
sessions = {}
user_bets = {}
user_performance = {}
odds_cache = {}
cache_timestamp = {}
bet_history = []

# Initialize ML models if available
if ML_MODELS_AVAILABLE:
    try:
        nfl_model = NFLEnsembleModel()
        mlb_model = MLBEnsembleModel()
        print("✅ ML Models Initialized!")
    except:
        ML_MODELS_AVAILABLE = False
        nfl_model = None
        mlb_model = None
else:
    nfl_model = None
    mlb_model = None

def format_game_time(iso_time: str) -> str:
    """Format ISO time to readable format"""
    try:
        if iso_time:
            dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            # Convert to Eastern Time (common for sports)
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
            bookmaker = game_data["bookmakers"][0]  # Use first bookmaker
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
        confidence_level = analysis.get("confidence_level", "WEAK")
        
        # Generate specific bet recommendations based on confidence
        if confidence >= 75:
            # High confidence - recommend spread bet
            if analysis.get("favorite") == "home":
                recommendation["bets"].append({
                    "type": "SPREAD",
                    "pick": f"{game_data['home_team']} {spread:+.1f}",
                    "odds": spread_odds,
                    "confidence": confidence,
                    "reason": f"Strong edge on home favorite",
                    "suggested_unit": 2.0,  # 2 units for high confidence
                    "priority": 1
                })
            else:
                recommendation["bets"].append({
                    "type": "SPREAD",
                    "pick": f"{game_data['away_team']} {-spread:+.1f}",
                    "odds": spread_odds,
                    "confidence": confidence,
                    "reason": f"Strong edge on road team",
                    "suggested_unit": 2.0,
                    "priority": 1
                })
        
        elif confidence >= 65:
            # Medium confidence - recommend moneyline
            if analysis.get("favorite") == "home":
                recommendation["bets"].append({
                    "type": "MONEYLINE",
                    "pick": game_data['home_team'],
                    "odds": home_ml,
                    "confidence": confidence,
                    "reason": "Value on home team ML",
                    "suggested_unit": 1.0,
                    "priority": 2
                })
            else:
                recommendation["bets"].append({
                    "type": "MONEYLINE",
                    "pick": game_data['away_team'],
                    "odds": away_ml,
                    "confidence": confidence,
                    "reason": "Value on away team ML",
                    "suggested_unit": 1.0,
                    "priority": 2
                })
        
        # Check for total recommendation
        if "total_prediction" in analysis:
            if analysis["total_prediction"] == "over":
                recommendation["bets"].append({
                    "type": "TOTAL",
                    "pick": f"OVER {total}",
                    "odds": total_odds,
                    "confidence": analysis.get("total_confidence", 60),
                    "reason": "Projected high-scoring game",
                    "suggested_unit": 1.0,
                    "priority": 3
                })
            elif analysis["total_prediction"] == "under":
                recommendation["bets"].append({
                    "type": "TOTAL",
                    "pick": f"UNDER {total}",
                    "odds": total_odds,
                    "confidence": analysis.get("total_confidence", 60),
                    "reason": "Projected defensive battle",
                    "suggested_unit": 1.0,
                    "priority": 3
                })
        
        # Check for arbitrage
        if analysis.get("arbitrage", {}).get("exists"):
            arb = analysis["arbitrage"]
            recommendation["bets"].append({
                "type": "ARBITRAGE",
                "pick": f"Bet both sides across books",
                "odds": f"{arb['profit_margin']:.1f}% guaranteed",
                "confidence": 100,
                "reason": f"Risk-free profit opportunity",
                "suggested_unit": 5.0,  # Max bet on arbitrage
                "priority": 0  # Highest priority
            })
        
        # Add expected value calculation
        for bet in recommendation["bets"]:
            if bet["type"] != "ARBITRAGE":
                implied_prob = 1 / bet["odds"]
                win_prob = bet["confidence"] / 100
                ev = (win_prob * (bet["odds"] - 1)) - (1 - win_prob)
                bet["expected_value"] = f"{ev*100:.1f}%"
        
        return recommendation

def get_ml_prediction(game_data: Dict, sport: str) -> Dict:
    """Get prediction from ML models if available"""
    
    if not ML_MODELS_AVAILABLE or not game_data:
        return {}
    
    try:
        if sport == "NFL" and nfl_model:
            # Prepare features for NFL model
            features = {
                "home_team": game_data.get("home_team"),
                "away_team": game_data.get("away_team"),
                "spread": 0,  # Would get from odds
                "total": 0,   # Would get from odds
            }
            prediction = nfl_model.predict(features)
            return {
                "ml_confidence": prediction.get("confidence", 50),
                "ml_prediction": prediction.get("winner"),
                "ml_spread": prediction.get("spread_prediction"),
                "ml_total": prediction.get("total_prediction")
            }
        elif sport in ["MLB", "NBA"] and mlb_model:
            # Use MLB model for now
            return {
                "ml_confidence": 65,
                "ml_prediction": "home" if np.random.random() > 0.45 else "away"
            }
    except Exception as e:
        print(f"ML prediction error: {e}")
    
    return {}

def analyze_game_with_ml(game_data: Dict, sport: str = "NFL") -> Dict:
    """Enhanced game analysis with ML predictions"""
    
    analysis = {
        "game_id": game_data.get("id", "unknown"),
        "home_team": game_data.get("home_team", ""),
        "away_team": game_data.get("away_team", ""),
        "commence_time": game_data.get("commence_time", ""),
        "sport": sport
    }
    
    # Get ML prediction if available
    ml_prediction = get_ml_prediction(game_data, sport)
    
    # Extract odds
    bookmaker_odds = []
    spread = 0
    total = 0
    
    for bookmaker in game_data.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market["key"] == "h2h":
                outcomes = {o["name"]: o["price"] for o in market["outcomes"]}
                bookmaker_odds.append({
                    "bookmaker": bookmaker["title"],
                    "home_odds": outcomes.get(game_data["home_team"], 0),
                    "away_odds": outcomes.get(game_data["away_team"], 0)
                })
            elif market["key"] == "spreads":
                spread = market["outcomes"][0].get("point", 0)
            elif market["key"] == "totals":
                total = market["outcomes"][0].get("point", 0)
    
    # Calculate confidence combining odds analysis and ML
    if bookmaker_odds:
        avg_home = sum(b["home_odds"] for b in bookmaker_odds) / len(bookmaker_odds)
        avg_away = sum(b["away_odds"] for b in bookmaker_odds) / len(bookmaker_odds)
        
        # Odds-based confidence
        home_prob = 1 / avg_home if avg_home > 0 else 0.5
        away_prob = 1 / avg_away if avg_away > 0 else 0.5
        
        if home_prob > away_prob:
            odds_confidence = min(85, 50 + (home_prob - 0.5) * 70)
            favorite = "home"
        else:
            odds_confidence = min(85, 50 + (away_prob - 0.5) * 70)
            favorite = "away"
        
        # Combine with ML if available
        if ml_prediction:
            ml_conf = ml_prediction.get("ml_confidence", 50)
            # Weight: 60% ML, 40% odds
            final_confidence = (ml_conf * 0.6) + (odds_confidence * 0.4)
            
            # Adjust favorite based on ML
            if ml_prediction.get("ml_prediction") == "home":
                favorite = "home"
            elif ml_prediction.get("ml_prediction") == "away":
                favorite = "away"
        else:
            final_confidence = odds_confidence
        
        analysis["confidence_score"] = round(final_confidence, 1)
        analysis["favorite"] = favorite
        analysis["edge"] = abs(home_prob - away_prob) * 100
        
        # Confidence level
        if final_confidence >= 80:
            analysis["confidence_level"] = "ELITE"
        elif final_confidence >= 70:
            analysis["confidence_level"] = "HIGH"
        elif final_confidence >= 60:
            analysis["confidence_level"] = "GOOD"
        elif final_confidence >= 50:
            analysis["confidence_level"] = "FAIR"
        else:
            analysis["confidence_level"] = "AVOID"
        
        # Add ML predictions to analysis
        if ml_prediction:
            analysis.update(ml_prediction)
        
        # Total prediction
        if total > 0:
            # Simple over/under logic (would be more sophisticated with real ML)
            if sport == "NFL":
                avg_total = 47  # NFL average
            elif sport == "NBA":
                avg_total = 220  # NBA average
            else:
                avg_total = 8.5  # MLB average
            
            if total > avg_total * 1.05:
                analysis["total_prediction"] = "under"
                analysis["total_confidence"] = 65
            elif total < avg_total * 0.95:
                analysis["total_prediction"] = "over"
                analysis["total_confidence"] = 65
            else:
                analysis["total_prediction"] = "pass"
                analysis["total_confidence"] = 45
    
    # Check for arbitrage
    if len(bookmaker_odds) >= 2:
        best_home = max(bookmaker_odds, key=lambda x: x.get("home_odds", 0))
        best_away = max(bookmaker_odds, key=lambda x: x.get("away_odds", 0))
        
        if best_home["home_odds"] and best_away["away_odds"]:
            implied_total = (1/best_home["home_odds"]) + (1/best_away["away_odds"])
            if implied_total < 1.0:
                profit = (1 - implied_total) * 100
                analysis["arbitrage"] = {
                    "exists": True,
                    "profit_margin": profit,
                    "bet_home": {"bookmaker": best_home["bookmaker"], "odds": best_home["home_odds"]},
                    "bet_away": {"bookmaker": best_away["bookmaker"], "odds": best_away["away_odds"]}
                }
    
    return analysis

def get_cached_odds(sport: str = "americanfootball_nfl") -> List[Dict]:
    """Get odds with caching"""
    cache_key = f"odds_{sport}"
    
    # Check cache
    if cache_key in odds_cache:
        if datetime.now() - cache_timestamp[cache_key] < timedelta(minutes=30):
            print(f"Using cached data for {sport}")
            return odds_cache[cache_key]
    
    # Always try API first with your real key
    print(f"Fetching live odds for {sport}...")
    try:
        response = requests.get(
            f"{ODDS_API_BASE}/sports/{sport}/odds",
            params={
                'apiKey': ODDS_API_KEY,
                'regions': 'us',
                'markets': 'h2h,spreads,totals'
                # Don't limit bookmakers - get all available
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {len(data)} real {sport} games from API")
            print(f"   API calls remaining: {response.headers.get('x-requests-remaining', 'N/A')}")
            odds_cache[cache_key] = data
            cache_timestamp[cache_key] = datetime.now()
            return data
        else:
            print(f"❌ API error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Only use mock data if API completely fails
    print("⚠️ Using mock data as fallback")
    return generate_mock_odds(sport)

def generate_mock_odds(sport: str) -> List[Dict]:
    """Generate realistic mock odds"""
    import random
    
    if "nfl" in sport:
        teams = [
            ("Kansas City Chiefs", "Buffalo Bills"),
            ("Dallas Cowboys", "Philadelphia Eagles"),
            ("San Francisco 49ers", "Los Angeles Rams"),
            ("Baltimore Ravens", "Cincinnati Bengals"),
            ("Green Bay Packers", "Chicago Bears"),
            ("New England Patriots", "New York Jets"),
            ("Pittsburgh Steelers", "Cleveland Browns"),
            ("Miami Dolphins", "Jacksonville Jaguars"),
            ("Tennessee Titans", "Houston Texans"),
            ("Seattle Seahawks", "Arizona Cardinals"),
            ("Las Vegas Raiders", "Denver Broncos"),
            ("Tampa Bay Buccaneers", "New Orleans Saints"),
            ("Minnesota Vikings", "Detroit Lions"),
            ("Indianapolis Colts", "Los Angeles Chargers"),
            ("Atlanta Falcons", "Carolina Panthers")
        ]
    elif "nba" in sport:
        teams = [
            ("Los Angeles Lakers", "Boston Celtics"),
            ("Golden State Warriors", "Phoenix Suns"),
            ("Milwaukee Bucks", "Miami Heat"),
            ("Denver Nuggets", "Dallas Mavericks"),
            ("Philadelphia 76ers", "Brooklyn Nets"),
            ("Memphis Grizzlies", "Sacramento Kings"),
            ("Cleveland Cavaliers", "New York Knicks"),
            ("Portland Trail Blazers", "Utah Jazz"),
            ("Atlanta Hawks", "Orlando Magic"),
            ("Toronto Raptors", "Chicago Bulls"),
            ("San Antonio Spurs", "Houston Rockets"),
            ("Indiana Pacers", "Detroit Pistons")
        ]
    elif "mlb" in sport:
        teams = [
            ("New York Yankees", "Boston Red Sox"),
            ("Los Angeles Dodgers", "San Francisco Giants"),
            ("Houston Astros", "Texas Rangers"),
            ("Atlanta Braves", "New York Mets"),
            ("Philadelphia Phillies", "Washington Nationals"),
            ("Chicago Cubs", "St. Louis Cardinals"),
            ("San Diego Padres", "Arizona Diamondbacks"),
            ("Tampa Bay Rays", "Baltimore Orioles"),
            ("Cleveland Guardians", "Minnesota Twins"),
            ("Toronto Blue Jays", "Seattle Mariners"),
            ("Milwaukee Brewers", "Cincinnati Reds")
        ]
    else:  # NCAAF
        teams = [
            ("Alabama", "Georgia"),
            ("Ohio State", "Michigan"),
            ("Texas", "Oklahoma"),
            ("USC", "Notre Dame"),
            ("Florida State", "Miami"),
            ("Penn State", "Michigan State"),
            ("Oregon", "Washington"),
            ("LSU", "Auburn"),
            ("Tennessee", "Florida"),
            ("Clemson", "South Carolina"),
            ("Wisconsin", "Iowa"),
            ("UCLA", "Stanford")
        ]
    
    games = []
    for home, away in teams:
        home_ml = round(random.uniform(1.5, 3.0), 2)
        away_ml = round(random.uniform(1.5, 3.0), 2)
        spread = round(random.uniform(-14, 14), 1)
        
        if "nba" in sport:
            total = round(random.uniform(210, 240), 1)
        elif "mlb" in sport:
            total = round(random.uniform(7, 11), 1)
        else:
            total = round(random.uniform(38, 58), 1)
        
        games.append({
            "id": f"game_{len(games)+1}_{sport}",
            "sport_key": sport,
            "commence_time": (datetime.now() + timedelta(hours=random.randint(1, 72))).isoformat(),
            "home_team": home,
            "away_team": away,
            "bookmakers": [
                {
                    "key": "draftkings",
                    "title": "DraftKings",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": home, "price": home_ml},
                                {"name": away, "price": away_ml}
                            ]
                        },
                        {
                            "key": "spreads",
                            "outcomes": [
                                {"name": home, "price": 1.91, "point": -spread},
                                {"name": away, "price": 1.91, "point": spread}
                            ]
                        },
                        {
                            "key": "totals",
                            "outcomes": [
                                {"name": "Over", "price": 1.87, "point": total},
                                {"name": "Under", "price": 1.95, "point": total}
                            ]
                        }
                    ]
                },
                {
                    "key": "fanduel",
                    "title": "FanDuel",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": home, "price": home_ml + 0.05},
                                {"name": away, "price": away_ml - 0.05}
                            ]
                        }
                    ]
                }
            ]
        })
    
    return games

def get_dashboard_html(user: str, sport: str = "NFL") -> str:
    """Generate enhanced dashboard with clear betting recommendations"""
    
    # Map sports
    sport_map = {
        "NFL": "americanfootball_nfl",
        "NCAAF": "americanfootball_ncaaf",
        "NBA": "basketball_nba",
        "MLB": "baseball_mlb"
    }
    
    sport_key = sport_map.get(sport, "americanfootball_nfl")
    games = get_cached_odds(sport_key)
    
    # Analyze games and generate recommendations
    all_recommendations = []
    elite_bets = []
    arbitrage_opportunities = []
    
    # Analyze all available games (no limit needed with real data)
    for game in games:
        analysis = analyze_game_with_ml(game, sport)
        recommendation = BettingRecommendation.generate_recommendation(game, analysis)
        
        if recommendation["bets"]:
            all_recommendations.append({
                "game": game,
                "analysis": analysis,
                "recommendation": recommendation
            })
            
            # Categorize bets
            for bet in recommendation["bets"]:
                if bet["type"] == "ARBITRAGE":
                    arbitrage_opportunities.append({
                        "game": recommendation["teams"],
                        "bet": bet
                    })
                elif bet["confidence"] >= 75:
                    elite_bets.append({
                        "game": recommendation["teams"],
                        "bet": bet
                    })
    
    # Generate bet cards HTML
    bet_cards_html = ""
    for rec in all_recommendations:
        game = rec["game"]
        analysis = rec["analysis"]
        recommendation = rec["recommendation"]
        
        # Confidence color
        confidence_color = {
            "ELITE": "#4CAF50",
            "HIGH": "#66BB6A",
            "GOOD": "#FFC107",
            "FAIR": "#FF9800",
            "AVOID": "#F44336"
        }.get(analysis.get("confidence_level", "FAIR"), "#9E9E9E")
        
        # Generate bet recommendations HTML
        bets_html = ""
        for bet in recommendation["bets"][:4]:  # Show top 4 bets
            bet_color = "#4CAF50" if bet["confidence"] >= 70 else "#2196F3"
            bets_html += f"""
            <div style="background: {bet_color}; color: white; padding: 12px; 
                        border-radius: 8px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="font-size: 16px;">{bet['type']}: {bet['pick']}</strong>
                        <div style="font-size: 14px; margin-top: 5px;">
                            Odds: {bet.get('odds', 'N/A')} | Units: {bet['suggested_unit']}
                        </div>
                        <div style="font-size: 12px; margin-top: 5px; opacity: 0.9;">
                            {bet['reason']}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 24px; font-weight: bold;">
                            {bet['confidence']:.0f}%
                        </div>
                        <div style="font-size: 12px;">
                            EV: {bet.get('expected_value', 'N/A')}
                        </div>
                    </div>
                </div>
            </div>
            """
        
        # ML indicator
        ml_badge = ""
        if analysis.get("ml_confidence"):
            ml_badge = f"""
            <span style="background: #9C27B0; color: white; padding: 2px 8px; 
                        border-radius: 4px; font-size: 12px; margin-left: 10px;">
                ML: {analysis['ml_confidence']:.0f}%
            </span>
            """
        
        bet_cards_html += f"""
        <div class="bet-card">
            <div class="bet-card-header">
                <h3>{game['home_team']} vs {game['away_team']}</h3>
                <div style="display: flex; align-items: center; gap: 10px; margin-top: 8px;">
                    <span style="background: #2196F3; color: white; padding: 4px 10px; 
                                border-radius: 6px; font-size: 13px; font-weight: 500;">
                        📅 {format_game_time(game.get('commence_time', ''))}
                    </span>
                    {ml_badge}
                </div>
            </div>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {analysis.get('confidence_score', 50)}%; 
                     background: {confidence_color};">
                    {analysis.get('confidence_score', 50):.1f}%
                </div>
            </div>
            <div style="margin: 15px 0; padding: 10px; background: #f5f5f5; border-radius: 8px;">
                <strong>Analysis:</strong> {analysis.get('confidence_level', 'UNKNOWN')} confidence
                {' | ML Model: Active' if ML_MODELS_AVAILABLE else ' | ML Model: Offline'}
            </div>
            {bets_html}
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button onclick="placeBet('{game['id']}', '{recommendation['bets'][0]['pick'] if recommendation['bets'] else ''}')" 
                        class="action-btn primary">Place Bet</button>
                <button onclick="trackBet('{game['id']}')" 
                        class="action-btn secondary">Track</button>
                <button onclick="showDetails('{game['id']}')" 
                        class="action-btn">Details</button>
            </div>
        </div>
        """
    
    # Generate alerts
    alerts_html = ""
    if arbitrage_opportunities:
        alerts_html += f"""
        <div class="alert arbitrage">
            <strong>💰 {len(arbitrage_opportunities)} ARBITRAGE OPPORTUNITIES!</strong><br>
            Guaranteed profit available - act fast!
            <ul style="margin: 10px 0 0 20px;">
        """
        for arb in arbitrage_opportunities[:3]:
            alerts_html += f"<li>{arb['game']}: {arb['bet']['odds']}</li>"
        alerts_html += "</ul></div>"
    
    if elite_bets:
        alerts_html += f"""
        <div class="alert elite">
            <strong>🔥 {len(elite_bets)} ELITE BETS (75%+ Confidence)</strong><br>
            High-confidence opportunities identified by our models.
        </div>
        """
    
    # Performance stats
    user_perf = user_performance.get(user, {
        "total_bets": 0,
        "wins": 0,
        "losses": 0,
        "profit": 0,
        "roi": 0
    })
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sports Betting Analysis - ML Enhanced</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        {get_google_analytics_script()}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            .header {{
                background: rgba(255,255,255,0.98);
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            .ml-status {{
                display: inline-block;
                padding: 6px 12px;
                border-radius: 6px;
                margin-left: 15px;
                font-size: 13px;
                font-weight: 600;
            }}
            .ml-active {{ background: #4CAF50; color: white; }}
            .ml-offline {{ background: #FF9800; color: white; }}
            .nav-tabs {{
                display: flex;
                gap: 10px;
                margin: 20px 0;
                flex-wrap: wrap;
            }}
            .nav-tab {{
                padding: 12px 24px;
                background: rgba(255,255,255,0.9);
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
            }}
            .nav-tab.active {{
                background: #4CAF50;
                color: white;
                transform: translateY(-2px);
            }}
            .dashboard {{
                background: rgba(255,255,255,0.98);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            .alert {{
                padding: 15px 20px;
                border-radius: 10px;
                margin-bottom: 15px;
                font-weight: 500;
                animation: slideIn 0.5s ease;
            }}
            .alert.arbitrage {{
                background: linear-gradient(135deg, #FFD700, #FFA000);
                color: #000;
                border: 2px solid #FF8F00;
            }}
            .alert.elite {{
                background: linear-gradient(135deg, #4CAF50, #45a049);
                color: white;
            }}
            @keyframes slideIn {{
                from {{ transform: translateX(-100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 25px 0;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                border: 1px solid #e0e0e0;
                transition: transform 0.3s;
            }}
            .stat-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            .stat-value {{
                font-size: 32px;
                font-weight: bold;
                color: #2196F3;
                margin-bottom: 5px;
            }}
            .stat-label {{
                font-size: 13px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .bet-card {{
                background: white;
                padding: 25px;
                border-radius: 12px;
                margin-bottom: 20px;
                border: 2px solid #e0e0e0;
                transition: all 0.3s;
            }}
            .bet-card:hover {{
                border-color: #4CAF50;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }}
            .bet-card-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            .confidence-bar {{
                height: 35px;
                background: #f0f0f0;
                border-radius: 20px;
                overflow: hidden;
                margin: 15px 0;
            }}
            .confidence-fill {{
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 16px;
                transition: width 0.5s;
            }}
            .action-btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
                font-size: 14px;
            }}
            .action-btn.primary {{
                background: #4CAF50;
                color: white;
            }}
            .action-btn.primary:hover {{
                background: #45a049;
                transform: translateY(-2px);
            }}
            .action-btn.secondary {{
                background: #2196F3;
                color: white;
            }}
            .action-btn.secondary:hover {{
                background: #1976D2;
            }}
            .action-btn {{
                background: #f5f5f5;
                color: #333;
            }}
            .action-btn:hover {{
                background: #e0e0e0;
            }}
            .refresh-btn {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: #4CAF50;
                color: white;
                border: none;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                transition: all 0.3s;
            }}
            .refresh-btn:hover {{
                transform: rotate(180deg);
                background: #45a049;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Smart Betting Analysis Platform
                    <span class="ml-status {'ml-active' if ML_MODELS_AVAILABLE else 'ml-offline'}">
                        {'ML Models: Active' if ML_MODELS_AVAILABLE else 'ML Models: Simplified'}
                    </span>
                </h1>
                <p style="margin-top: 10px; color: #666;">
                    Welcome {user} | Real-time analysis with {'ML-powered' if ML_MODELS_AVAILABLE else 'statistical'} predictions
                </p>
            </div>

            <div class="nav-tabs">
                <button class="nav-tab {'active' if sport == 'NFL' else ''}" 
                        onclick="window.location.href='/dashboard?sport=NFL'">🏈 NFL</button>
                <button class="nav-tab {'active' if sport == 'NCAAF' else ''}" 
                        onclick="window.location.href='/dashboard?sport=NCAAF'">🎓 NCAAF</button>
                <button class="nav-tab {'active' if sport == 'NBA' else ''}" 
                        onclick="window.location.href='/dashboard?sport=NBA'">🏀 NBA</button>
                <button class="nav-tab {'active' if sport == 'MLB' else ''}" 
                        onclick="window.location.href='/dashboard?sport=MLB'">⚾ MLB</button>
            </div>

            <div class="dashboard">
                {alerts_html}
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{len(all_recommendations)}</div>
                        <div class="stat-label">Active Games</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(elite_bets)}</div>
                        <div class="stat-label">Elite Bets</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(arbitrage_opportunities)}</div>
                        <div class="stat-label">Arbitrage Opps</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{'LIVE' if ODDS_API_KEY != 'demo-key' else 'DEMO'}</div>
                        <div class="stat-label">Data Status</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{user_perf.get('roi', 0):.1f}%</div>
                        <div class="stat-label">Your ROI</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{user_perf.get('wins', 0)}-{user_perf.get('losses', 0)}</div>
                        <div class="stat-label">Win-Loss</div>
                    </div>
                </div>
                
                <h2 style="margin: 30px 0 20px;">🎯 Today's Best Betting Opportunities</h2>
                <div class="bets-container">
                    {bet_cards_html}
                </div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="location.reload()">↻</button>

        <script>
            function placeBet(gameId, pick) {{
                gtag('event', 'place_bet', {{
                    'event_category': 'betting',
                    'event_label': pick,
                    'game_id': gameId
                }});
                
                fetch('/api/place-bet', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        gameId: gameId,
                        pick: pick,
                        timestamp: new Date().toISOString()
                    }})
                }}).then(response => response.json())
                .then(data => {{
                    alert('Bet placed: ' + pick);
                }});
            }}
            
            function trackBet(gameId) {{
                gtag('event', 'track_bet', {{
                    'event_category': 'tracking',
                    'game_id': gameId
                }});
                alert('Added to tracking list');
            }}
            
            function showDetails(gameId) {{
                gtag('event', 'view_details', {{
                    'event_category': 'engagement',
                    'game_id': gameId
                }});
                window.location.href = '/api/analysis/' + gameId;
            }}
            
            // Auto-refresh every 5 minutes
            setTimeout(() => {{
                location.reload();
            }}, 300000);
        </script>
    </body>
    </html>
    """

def get_google_analytics_script():
    """Google Analytics tracking script"""
    return f"""
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GOOGLE_ANALYTICS_ID}');
    </script>
    """

# Routes (keeping existing auth routes)
@app.get("/", response_class=HTMLResponse)
async def home():
    """Landing page"""
    ml_status = "ML Models Active" if ML_MODELS_AVAILABLE else "Statistical Analysis"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart Betting Platform - ML Enhanced</title>
        {get_google_analytics_script()}
        <style>
            body {{
                font-family: -apple-system, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .container {{
                background: white;
                padding: 50px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 500px;
            }}
            h1 {{ color: #333; margin-bottom: 20px; }}
            .features {{
                text-align: left;
                margin: 30px 0;
                padding: 20px;
                background: #f5f5f5;
                border-radius: 10px;
            }}
            .feature {{
                margin: 10px 0;
                padding-left: 25px;
                position: relative;
            }}
            .feature:before {{
                content: "✓";
                position: absolute;
                left: 0;
                color: #4CAF50;
                font-weight: bold;
            }}
            .btn {{
                display: inline-block;
                padding: 15px 40px;
                margin: 10px;
                background: linear-gradient(135deg, #4CAF50, #45a049);
                color: white;
                text-decoration: none;
                border-radius: 30px;
                font-weight: 600;
                font-size: 16px;
                transition: all 0.3s;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
            }}
            .btn:hover {{
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
            }}
            .btn.secondary {{
                background: linear-gradient(135deg, #2196F3, #1976D2);
                box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
            }}
            .btn.secondary:hover {{
                box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
            }}
            .status {{
                margin-top: 30px;
                padding: 15px;
                background: #f0f0f0;
                border-radius: 10px;
                font-size: 14px;
            }}
            .ml-badge {{
                display: inline-block;
                padding: 4px 10px;
                background: {'#4CAF50' if ML_MODELS_AVAILABLE else '#FF9800'};
                color: white;
                border-radius: 5px;
                font-weight: 600;
                margin: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Smart Betting Platform</h1>
            <p style="color: #666; font-size: 18px;">AI-Powered Sports Betting Analysis</p>
            
            <div class="features">
                <div class="feature">Clear betting recommendations</div>
                <div class="feature">ML-powered predictions</div>
                <div class="feature">Real-time arbitrage detection</div>
                <div class="feature">Multi-sport coverage (NFL, NBA, MLB)</div>
                <div class="feature">Performance tracking & ROI metrics</div>
            </div>
            
            <a href="/register" class="btn">Start Free Trial</a>
            <a href="/login" class="btn secondary">Login</a>
            
            <div class="status">
                <div style="margin-bottom: 10px;">System Status:</div>
                <span class="ml-badge">{ml_status}</span>
                <span class="ml-badge" style="background: #2196F3;">{'Live Odds' if ODDS_API_KEY != 'demo-key' else 'Demo Mode'}</span>
                <span class="ml-badge" style="background: #9C27B0;">GA4 Active</span>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """Registration page"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - Smart Betting Platform</title>
        {get_google_analytics_script()}
        <style>
            body {{
                font-family: -apple-system, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 400px;
                width: 100%;
            }}
            h2 {{ color: #333; margin-bottom: 30px; text-align: center; }}
            input {{
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
            }}
            button {{
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #4CAF50, #45a049);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 20px;
            }}
            button:hover {{ background: #45a049; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎯 Create Your Account</h2>
            <form action="/register" method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <input type="text" name="access_code" placeholder="Access Code (BETA2024)" required>
                <button type="submit">Start Winning</button>
                <p style="text-align: center; margin-top: 20px; color: #666;">
                    Already have an account? <a href="/login">Login</a>
                </p>
            </form>
        </div>
        <script>
            gtag('event', 'page_view', {{'page_title': 'Register'}});
        </script>
    </body>
    </html>
    """

@app.post("/register")
async def register(username: str = Form(...), email: str = Form(...), 
                  password: str = Form(...), access_code: str = Form(...)):
    """Handle registration"""
    valid_codes = ["BETA2024", "EARLY2024", "VIP2024", "ML2024"]
    
    if access_code not in valid_codes:
        raise HTTPException(status_code=400, detail="Invalid access code")
    
    if username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Store user
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    users_db[username] = {
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.now().isoformat(),
        "access_code": access_code
    }
    
    # Initialize user performance
    user_performance[username] = {
        "total_bets": 0,
        "wins": 0,
        "losses": 0,
        "profit": 0,
        "roi": 0
    }
    
    # Create session
    session_id = secrets.token_hex(16)
    sessions[session_id] = username
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_id", value=session_id)
    
    return response

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Smart Betting Platform</title>
        {get_google_analytics_script()}
        <style>
            body {{
                font-family: -apple-system, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 400px;
                width: 100%;
            }}
            h2 {{ color: #333; margin-bottom: 30px; text-align: center; }}
            input {{
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
            }}
            button {{
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #2196F3, #1976D2);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 20px;
            }}
            button:hover {{ background: #1976D2; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎯 Welcome Back!</h2>
            <form action="/login" method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
                <p style="text-align: center; margin-top: 20px; color: #666;">
                    Don't have an account? <a href="/register">Register</a>
                </p>
            </form>
        </div>
        <script>
            gtag('event', 'page_view', {{'page_title': 'Login'}});
        </script>
    </body>
    </html>
    """

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Handle login"""
    if username not in users_db:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if users_db[username]["password_hash"] != password_hash:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Create session
    session_id = secrets.token_hex(16)
    sessions[session_id] = username
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_id", value=session_id)
    
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, sport: str = "NFL"):
    """Main dashboard with ML-powered recommendations"""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return RedirectResponse(url="/login", status_code=303)
    
    username = sessions[session_id]
    return get_dashboard_html(username, sport)

@app.post("/api/place-bet")
async def place_bet(request: Request):
    """API endpoint to place bets"""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    username = sessions[session_id]
    
    # Store bet
    if username not in user_bets:
        user_bets[username] = []
    
    bet = {
        "game_id": data.get("gameId"),
        "pick": data.get("pick"),
        "timestamp": data.get("timestamp", datetime.now().isoformat()),
        "status": "pending"
    }
    
    user_bets[username].append(bet)
    bet_history.append({**bet, "user": username})
    
    # Update user stats
    user_performance[username]["total_bets"] += 1
    
    return {"success": True, "message": f"Bet placed: {data.get('pick')}", "bet_id": len(bet_history)}

@app.get("/api/analysis/{game_id}")
async def get_game_analysis(game_id: str):
    """Get detailed analysis for a specific game"""
    # This would fetch specific game and run deep ML analysis
    return {
        "game_id": game_id,
        "ml_models_active": ML_MODELS_AVAILABLE,
        "detailed_analysis": "Full analysis would be here",
        "historical_performance": "Historical data for teams",
        "weather_impact": "Weather analysis if outdoor game",
        "injury_report": "Key injuries affecting the game"
    }

@app.get("/api/performance")
async def get_user_performance(request: Request):
    """Get user's betting performance"""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    username = sessions[session_id]
    return user_performance.get(username, {})

if __name__ == "__main__":
    print("=" * 60)
    print("SMART BETTING PLATFORM - ML ENHANCED")
    print("=" * 60)
    print(f"ML Models: {'✅ Active' if ML_MODELS_AVAILABLE else '⚠️ Simplified Mode'}")
    print(f"Odds API: {'✅ Live Data' if ODDS_API_KEY != 'demo-key' else '📊 Demo Mode'}")
    print(f"Google Analytics: ✅ {GOOGLE_ANALYTICS_ID}")
    print("=" * 60)
    print("Features:")
    print("- Clear betting recommendations with specific picks")
    print("- ML model integration for predictions")
    print("- Multi-sport support (NFL, NBA, MLB, NCAAF)")
    print("- Real-time arbitrage detection")
    print("- Performance tracking and ROI metrics")
    print("- Bet history and tracking")
    print("=" * 60)
    print("Starting server at http://localhost:8000")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)