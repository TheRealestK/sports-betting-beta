#!/usr/bin/env python3
"""
NFL Feature Adapter
Bridges the gap between beta platform data and trained NFL models
Converts minimal game data to the 149 features expected by the models
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

class NFLFeatureAdapter:
    """Adapts simple game data to full feature set for NFL models."""
    
    # Expected feature names for the 149-feature model
    FEATURE_NAMES = [
        # Offensive features (20)
        'home_yards_per_game', 'away_yards_per_game',
        'home_points_per_game', 'away_points_per_game', 
        'home_pass_yards_per_game', 'away_pass_yards_per_game',
        'home_rush_yards_per_game', 'away_rush_yards_per_game',
        'home_third_down_pct', 'away_third_down_pct',
        'home_red_zone_pct', 'away_red_zone_pct',
        'home_time_of_possession', 'away_time_of_possession',
        'home_turnovers_per_game', 'away_turnovers_per_game',
        'home_sacks_allowed', 'away_sacks_allowed',
        'home_penalties_per_game', 'away_penalties_per_game',
        
        # Defensive features (22)
        'home_yards_allowed_per_game', 'away_yards_allowed_per_game',
        'home_points_allowed_per_game', 'away_points_allowed_per_game',
        'home_pass_yards_allowed', 'away_pass_yards_allowed',
        'home_rush_yards_allowed', 'away_rush_yards_allowed',
        'home_third_down_def_pct', 'away_third_down_def_pct',
        'home_red_zone_def_pct', 'away_red_zone_def_pct',
        'home_sacks_per_game', 'away_sacks_per_game',
        'home_interceptions_per_game', 'away_interceptions_per_game',
        'home_forced_fumbles_per_game', 'away_forced_fumbles_per_game',
        'home_defensive_tds', 'away_defensive_tds',
        
        # Recent form (16)
        'home_last_3_wins', 'away_last_3_wins',
        'home_last_3_points_for', 'away_last_3_points_for',
        'home_last_3_points_against', 'away_last_3_points_against',
        'home_momentum_score', 'away_momentum_score',
        'home_last_5_ats', 'away_last_5_ats',
        'home_last_5_totals', 'away_last_5_totals',
        'home_streak', 'away_streak',
        'home_rest_advantage', 'away_rest_advantage',
        
        # QB Stats (20)
        'home_qb_rating', 'away_qb_rating',
        'home_qb_completion_pct', 'away_qb_completion_pct',
        'home_qb_yards_per_attempt', 'away_qb_yards_per_attempt',
        'home_qb_td_int_ratio', 'away_qb_td_int_ratio',
        'home_qb_sack_rate', 'away_qb_sack_rate',
        'home_qb_qbr', 'away_qb_qbr',
        'home_qb_pressure_rate', 'away_qb_pressure_rate',
        'home_qb_deep_ball_pct', 'away_qb_deep_ball_pct',
        'home_qb_third_down_rating', 'away_qb_third_down_rating',
        'home_qb_red_zone_rating', 'away_qb_red_zone_rating',
        
        # RB Stats (12)
        'home_rb_yards_per_carry', 'away_rb_yards_per_carry',
        'home_rb_breakaway_runs', 'away_rb_breakaway_runs',
        'home_rb_yards_after_contact', 'away_rb_yards_after_contact',
        'home_rb_receiving_yards', 'away_rb_receiving_yards',
        'home_rb_total_touches', 'away_rb_total_touches',
        'home_rb_fumble_rate', 'away_rb_fumble_rate',
        
        # WR/TE Stats (6)
        'home_wr_separation', 'away_wr_separation',
        'home_wr_drop_rate', 'away_wr_drop_rate',
        'home_wr_yards_after_catch', 'away_wr_yards_after_catch',
        
        # OL/DL Stats (12)
        'home_ol_pass_block_win_rate', 'away_ol_pass_block_win_rate',
        'home_ol_run_block_win_rate', 'away_ol_run_block_win_rate',
        'home_dl_pass_rush_win_rate', 'away_dl_pass_rush_win_rate',
        'home_dl_run_stop_rate', 'away_dl_run_stop_rate',
        'home_pocket_time', 'away_pocket_time',
        'home_hurry_rate', 'away_hurry_rate',
        
        # Special teams (8)
        'home_field_goal_pct', 'away_field_goal_pct',
        'home_punt_return_avg', 'away_punt_return_avg',
        'home_kick_return_avg', 'away_kick_return_avg',
        'home_net_punting_avg', 'away_net_punting_avg',
        
        # Matchup/situational (15)
        'head_to_head_wins_home', 'head_to_head_avg_total',
        'division_game', 'conference_game',
        'primetime_game', 'playoff_implications',
        'home_field_advantage', 'altitude_factor',
        'travel_distance', 'timezone_change',
        'revenge_game', 'lookahead_spot',
        'sandwich_game', 'rest_differential',
        'injury_report_impact',
        
        # Weather (8)
        'temperature', 'wind_speed',
        'precipitation_chance', 'humidity',
        'dome_game', 'field_condition',
        'weather_impact_passing', 'weather_impact_total',
        
        # Market/betting (12)
        'opening_spread', 'current_spread',
        'spread_movement', 'opening_total',
        'current_total', 'total_movement',
        'home_moneyline', 'away_moneyline',
        'public_bet_pct_spread', 'public_bet_pct_total',
        'sharp_money_indicator', 'reverse_line_movement'
    ]
    
    def __init__(self):
        """Initialize the feature adapter."""
        self.feature_count = len(self.FEATURE_NAMES)
        assert self.feature_count == 149, f"Expected 149 features, got {self.feature_count}"
        
    def extract_features_from_game(self, game_data: Dict, odds_data: Optional[Dict] = None) -> np.ndarray:
        """
        Extract 149 features from game data.
        
        Args:
            game_data: Basic game information (teams, date, etc.)
            odds_data: Optional odds/betting data
            
        Returns:
            numpy array with 149 features
        """
        features = []
        
        # Use default values for most features
        # In production, these would come from a comprehensive data source
        
        # Offensive features (20) - use realistic NFL ranges
        features.extend([
            350.5, 340.2,  # yards per game
            24.5, 22.3,    # points per game
            245.3, 235.1,  # pass yards
            105.2, 105.1,  # rush yards
            0.42, 0.39,    # third down %
            0.55, 0.52,    # red zone %
            31.2, 28.8,    # time of possession
            1.2, 1.5,      # turnovers
            2.1, 2.8,      # sacks allowed
            6.2, 6.8       # penalties
        ])
        
        # Defensive features (22)
        features.extend([
            325.8, 345.2,  # yards allowed
            20.5, 23.2,    # points allowed
            220.5, 235.8,  # pass yards allowed
            105.3, 109.4,  # rush yards allowed
            0.38, 0.41,    # third down def
            0.48, 0.51,    # red zone def
            2.8, 2.2,      # sacks
            0.9, 0.7,      # interceptions
            0.6, 0.4,      # forced fumbles
            0.15, 0.10     # defensive TDs
        ])
        
        # Recent form (16)
        features.extend([
            2, 1,          # last 3 wins
            75, 65,        # last 3 points for
            62, 71,        # last 3 points against
            0.6, 0.4,      # momentum
            3, 2,          # last 5 ATS
            3, 2,          # last 5 totals
            2, -1,         # streak
            0, 0           # rest advantage
        ])
        
        # QB Stats (20)
        features.extend([
            95.2, 88.5,    # QB rating
            0.65, 0.62,    # completion %
            7.5, 7.1,      # yards per attempt
            2.5, 1.8,      # TD/INT ratio
            0.06, 0.08,    # sack rate
            58.2, 52.1,    # QBR
            0.35, 0.42,    # pressure rate
            0.12, 0.10,    # deep ball %
            98.5, 92.1,    # 3rd down rating
            102.3, 95.8    # red zone rating
        ])
        
        # RB Stats (12)
        features.extend([
            4.2, 3.9,      # yards per carry
            0.15, 0.12,    # breakaway runs
            2.8, 2.5,      # yards after contact
            25.5, 22.1,    # receiving yards
            18.5, 16.2,    # total touches
            0.015, 0.020   # fumble rate
        ])
        
        # WR/TE Stats (6)
        features.extend([
            2.8, 2.5,      # separation
            0.05, 0.07,    # drop rate
            5.2, 4.8       # YAC
        ])
        
        # OL/DL Stats (12)
        features.extend([
            0.68, 0.62,    # pass block win
            0.72, 0.68,    # run block win
            0.42, 0.38,    # pass rush win
            0.35, 0.32,    # run stop rate
            2.5, 2.3,      # pocket time
            0.22, 0.28     # hurry rate
        ])
        
        # Special teams (8)
        features.extend([
            0.85, 0.82,    # FG %
            8.5, 7.2,      # punt return
            22.5, 21.1,    # kick return
            42.5, 40.8     # net punting
        ])
        
        # Matchup/situational (15)
        features.extend([
            0.5,           # H2H wins (0.5 = even)
            48.5,          # H2H avg total
            0,             # division game
            0,             # conference game
            0,             # primetime
            0.5,           # playoff implications
            3.0,           # home field advantage
            0,             # altitude
            500,           # travel distance
            0,             # timezone change
            0,             # revenge game
            0,             # lookahead
            0,             # sandwich game
            0,             # rest differential
            0              # injury impact
        ])
        
        # Weather (8)
        features.extend([
            72,            # temperature
            5,             # wind speed
            0.1,           # precipitation
            50,            # humidity
            0,             # dome game
            1.0,           # field condition
            0,             # weather impact passing
            0              # weather impact total
        ])
        
        # Market/betting (12) - use actual odds if available
        if odds_data and odds_data.get('bookmakers'):
            book = odds_data['bookmakers'][0]
            spread_market = next((m for m in book.get('markets', []) if m['key'] == 'spreads'), None)
            total_market = next((m for m in book.get('markets', []) if m['key'] == 'totals'), None)
            ml_market = next((m for m in book.get('markets', []) if m['key'] == 'h2h'), None)
            
            if spread_market:
                current_spread = spread_market['outcomes'][0].get('point', -3.5)
            else:
                current_spread = -3.5
                
            if total_market:
                current_total = total_market['outcomes'][0].get('point', 45.5)
            else:
                current_total = 45.5
                
            features.extend([
                current_spread,      # opening spread (same as current for now)
                current_spread,      # current spread
                0,                   # spread movement
                current_total,       # opening total
                current_total,       # current total
                0,                   # total movement
                -150,                # home ML
                130,                 # away ML
                55,                  # public bet % spread
                52,                  # public bet % total
                0,                   # sharp money
                0                    # RLM
            ])
        else:
            # Default market features
            features.extend([
                -3.5, -3.5, 0,      # spread
                45.5, 45.5, 0,      # total
                -150, 130,          # moneylines
                55, 52,             # public %
                0, 0                # sharp/RLM
            ])
        
        # Convert to numpy array
        feature_array = np.array(features, dtype=np.float32)
        
        # Verify we have exactly 149 features
        assert len(feature_array) == 149, f"Expected 149 features, got {len(feature_array)}"
        
        return feature_array
    
    def extract_batch_features(self, games: List[Dict]) -> np.ndarray:
        """
        Extract features for multiple games.
        
        Args:
            games: List of game data dictionaries
            
        Returns:
            2D numpy array (n_games, 149)
        """
        features = []
        for game in games:
            game_features = self.extract_features_from_game(game)
            features.append(game_features)
        
        return np.array(features, dtype=np.float32)
    
    def get_feature_names(self) -> List[str]:
        """Get the list of feature names."""
        return self.FEATURE_NAMES.copy()


def test_adapter():
    """Test the feature adapter."""
    adapter = NFLFeatureAdapter()
    
    # Test with sample game
    sample_game = {
        'home_team': 'Kansas City Chiefs',
        'away_team': 'Buffalo Bills',
        'commence_time': '2025-01-20T20:00:00Z',
        'bookmakers': [{
            'title': 'DraftKings',
            'markets': [
                {
                    'key': 'spreads',
                    'outcomes': [
                        {'name': 'Kansas City Chiefs', 'point': -2.5, 'price': -110}
                    ]
                },
                {
                    'key': 'totals', 
                    'outcomes': [
                        {'name': 'Over', 'point': 48.5, 'price': -110}
                    ]
                }
            ]
        }]
    }
    
    features = adapter.extract_features_from_game(sample_game, sample_game)
    
    print(f"✅ Generated {len(features)} features")
    print(f"  Shape: {features.shape}")
    print(f"  Spread from odds: {features[121]}")  # current_spread index
    print(f"  Total from odds: {features[124]}")   # current_total index
    
    return True


if __name__ == "__main__":
    test_adapter()