#!/usr/bin/env python3
"""
Test script for OU_3 No Score Alert - Mock Data Testing
========================================================

This script creates mock match data to test all three criteria:
1. O/U line >= 3.0
2. Half-time break status (ID = 3)
3. Scoreless at half-time (0-0)
"""

import json
import sys
from pathlib import Path

# Add the current directory to path so we can import the alert module
sys.path.append(str(Path(__file__).parent))

from ou_3_no_score import (
    is_half_time_match,
    is_scoreless_at_halftime,
    get_status_description
)

def create_mock_matches():
    """Create mock match data for testing"""
    
    mock_matches = {
        # TEST 1: Perfect match - meets all 3 criteria
        "match_001": {
            "match_id": "test_001",
            "home_team": "Test Team A", 
            "away_team": "Test Team B",
            "home_score": 0,  # Scoreless ✓
            "away_score": 0,  # Scoreless ✓
            "status_id": 3,   # Half-time break ✓
            "over_under": {
                "line_1": {
                    "line": 3.5,  # >= 3.0 ✓
                    "over_odds": -110,
                    "under_odds": -110
                }
            },
            "competition": "Test League",
            "country": "Test Country"
        },
        
        # TEST 2: Fails scoreless criteria (1-0)
        "match_002": {
            "match_id": "test_002",
            "home_team": "Test Team C",
            "away_team": "Test Team D", 
            "home_score": 1,  # NOT scoreless ✗
            "away_score": 0,
            "status_id": 3,   # Half-time break ✓
            "over_under": {
                "line_1": {
                    "line": 3.0,  # >= 3.0 ✓
                    "over_odds": -105,
                    "under_odds": -115
                }
            }
        },
        
        # TEST 3: Fails status criteria (First half, not half-time)
        "match_003": {
            "match_id": "test_003",
            "home_team": "Test Team E",
            "away_team": "Test Team F",
            "home_score": 0,  # Scoreless ✓
            "away_score": 0,  # Scoreless ✓
            "status_id": 2,   # First half ✗ (should be 3)
            "over_under": {
                "line_1": {
                    "line": 3.25, # >= 3.0 ✓
                    "over_odds": +100,
                    "under_odds": -120
                }
            }
        },
        
        # TEST 4: Fails O/U line criteria (2.5 < 3.0)
        "match_004": {
            "match_id": "test_004",
            "home_team": "Test Team G",
            "away_team": "Test Team H",
            "home_score": 0,  # Scoreless ✓
            "away_score": 0,  # Scoreless ✓
            "status_id": 3,   # Half-time break ✓
            "over_under": {
                "line_1": {
                    "line": 2.5,  # < 3.0 ✗
                    "over_odds": -110,
                    "under_odds": -110
                }
            }
        },
        
        # TEST 5: Another perfect match
        "match_005": {
            "match_id": "test_005",
            "home_team": "Test Team I",
            "away_team": "Test Team J",
            "home_score": 0,  # Scoreless ✓
            "away_score": 0,  # Scoreless ✓ 
            "status_id": 3,   # Half-time break ✓
            "over_under": {
                "line_1": {
                    "line": 4.0,  # >= 3.0 ✓
                    "over_odds": +105,
                    "under_odds": -125
                }
            }
        }
    }
    
    return mock_matches

def test_individual_criteria():
    """Test each criteria function individually"""
    print("="*80)
    print("TESTING INDIVIDUAL CRITERIA FUNCTIONS")
    print("="*80)
    
    mock_matches = create_mock_matches()
    
    for match_id, match_data in mock_matches.items():
        print(f"\n--- Testing {match_id}: {match_data['home_team']} vs {match_data['away_team']} ---")
        
        # Test 1: Half-time status
        is_halftime = is_half_time_match(match_data)
        status_desc = get_status_description(match_data.get('status_id'))
        print(f"1. Half-time Status: {'✓' if is_halftime else '✗'} (ID: {match_data.get('status_id')} = {status_desc})")
        
        # Test 2: Scoreless check
        is_scoreless = is_scoreless_at_halftime(match_data)
        score = f"{match_data.get('home_score')}-{match_data.get('away_score')}"
        print(f"2. Scoreless (0-0): {'✓' if is_scoreless else '✗'} (Score: {score})")
        
        # Test 3: O/U line check
        over_under = match_data.get("over_under", {})
        has_qualifying_line = False
        line_value = None
        
        if over_under and isinstance(over_under, dict):
            for line_key, line_data in over_under.items():
                if isinstance(line_data, dict):
                    line_value = line_data.get("line")
                    if line_value and line_value >= 3.0:
                        has_qualifying_line = True
                        break
        
        print(f"3. O/U Line >= 3.0: {'✓' if has_qualifying_line else '✗'} (Line: {line_value})")
        
        # Overall result
        all_criteria_met = is_halftime and is_scoreless and has_qualifying_line
        print(f"OVERALL RESULT: {'✓ QUALIFIES' if all_criteria_met else '✗ FAILS'}")

def test_alert_logic():
    """Test the main alert logic with mock data"""
    print("\n" + "="*80)
    print("TESTING MAIN ALERT LOGIC")
    print("="*80)
    
    mock_matches = create_mock_matches()
    
    # Simulate the main scanning logic
    qualifying_matches = []
    min_line = 3.0
    
    print(f"\nScanning {len(mock_matches)} mock matches for:")
    print(f"  1. O/U lines >= {min_line}")
    print(f"  2. Half-time break status (ID=3)")
    print(f"  3. Scoreless at half-time (0-0)")
    print()
    
    for match_id, match_data in mock_matches.items():
        print(f"Checking {match_id}: {match_data['home_team']} vs {match_data['away_team']}")
        
        # Check 1: Half-time status
        if not is_half_time_match(match_data):
            print(f"  ✗ Not at half-time (Status ID: {match_data.get('status_id')})")
            continue
        print(f"  ✓ At half-time break")
        
        # Check 2: Scoreless
        if not is_scoreless_at_halftime(match_data):
            score = f"{match_data.get('home_score')}-{match_data.get('away_score')}"
            print(f"  ✗ Not scoreless (Score: {score})")
            continue
        print(f"  ✓ Scoreless (0-0)")
        
        # Check 3: O/U line
        over_under = match_data.get("over_under", {})
        has_qualifying_line = False
        
        if over_under and isinstance(over_under, dict):
            for line_key, line_data in over_under.items():
                if isinstance(line_data, dict):
                    line_value = line_data.get("line")
                    if line_value and line_value >= min_line:
                        has_qualifying_line = True
                        print(f"  ✓ Qualifying O/U line: {line_value}")
                        break
        
        if not has_qualifying_line:
            print(f"  ✗ No qualifying O/U lines >= {min_line}")
            continue
            
        # If we get here, all criteria are met
        qualifying_matches.append(match_data)
        print(f"  🎯 MATCH QUALIFIES FOR ALERT!")
        print()
    
    print(f"\nRESULT: {len(qualifying_matches)} of {len(mock_matches)} matches qualify for alert")
    print(f"Expected: 2 matches should qualify (match_001 and match_005)")
    
    if len(qualifying_matches) == 2:
        print("✅ TEST PASSED - Correct number of matches found!")
    else:
        print("❌ TEST FAILED - Unexpected number of matches")
        
    return qualifying_matches

if __name__ == "__main__":
    print("OU_3 No Score Alert - Mock Data Test")
    print("="*80)
    
    # Test individual functions
    test_individual_criteria()
    
    # Test main logic
    qualifying_matches = test_alert_logic()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
