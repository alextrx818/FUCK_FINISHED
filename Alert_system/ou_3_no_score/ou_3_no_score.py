#!/usr/bin/env python3
"""
OU_3 No Score Alert - Over/Under 3.0+ Scoreless Half Time Monitor
================================================================

Monitors matches with over/under lines of 3.0 or higher during HALF TIME ONLY
AND the game must be scoreless (0-0) at half time.

This alert specifically targets matches at half time (status ID = 3) with qualifying O/U lines
AND a scoreless half time score of 0-0.

This alert scans step5 data for matches that have over/under betting lines
of 3.0 or higher AND are currently at half time status AND are scoreless (0-0).

CRITERIA:
1. O/U line >= 3.0
2. Status ID = 3 (Half-time break)  
3. Score = 0-0 at half time
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Use Eastern timezone (same as step6)
TZ = ZoneInfo("America/New_York")

# Path constants
BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "ou_3_no_score.log"
CONFIG_FILE = BASE_DIR / "ou_3_no_score.json"
PROCESSED_MATCHES_FILE = BASE_DIR / "processed_matches.json"
DAILY_COUNTER_FILE = BASE_DIR / "daily_alert_count.json"

# Step5 data location
STEP5_JSON = Path("/root/CascadeProjects/Football_bot/step5/step5.json")

# Half Time specific status ID
HALF_TIME_STATUS_ID = 3  # Half-time break only

def get_eastern_time():
    """Get current Eastern time formatted string (same as step6)"""
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")

def setup_logging():
    """Setup logging that writes to ou_3_no_score.log"""
    logger = logging.getLogger("OU3_NoScore_Alert")
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # File handler only (no console output)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    
    # Simple format (no timestamp prefix since we add our own)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

def log_and_print(message):
    """Log message to file and print to console (same as step6)"""
    logger.info(message)
    print(message)

def get_and_increment_daily_count():
    """Get current daily alert count and increment for each new alert"""
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    
    try:
        with open(DAILY_COUNTER_FILE, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"date": today, "count": 0}
    
    # Reset count if it's a new day
    if data.get("date") != today:
        data = {"date": today, "count": 0}
    
    return data["count"], today

def save_daily_count(count, date):
    """Save the updated daily count"""
    try:
        data = {"date": date, "count": count, "last_updated": get_eastern_time()}
        with open(DAILY_COUNTER_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"OU3 No Score Alert: Error saving daily count: {e}")

def load_processed_matches():
    """Load the list of matches we've already processed"""
    try:
        with open(PROCESSED_MATCHES_FILE, 'r') as f:
            data = json.load(f)
            # Convert list to set for faster lookups
            processed_list = data.get("processed_matches", [])
            return set(processed_list), data.get("last_fetch_time", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return set(), ""

def save_processed_matches(processed_matches, fetch_time):
    """Save the list of processed matches and fetch time"""
    try:
        data = {
            "processed_matches": list(processed_matches),
            "last_fetch_time": fetch_time,
            "last_updated": get_eastern_time()
        }
        with open(PROCESSED_MATCHES_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"OU3 No Score Alert: Error saving processed matches: {e}")

def is_half_time_match(match_data):
    """Check if match is at half time (status ID = 3)"""
    status_id = match_data.get("status_id")
    return status_id == HALF_TIME_STATUS_ID

def is_scoreless_at_halftime(match_data):
    """Check if match is scoreless (0-0) at half time"""
    home_score = match_data.get("home_score", 0)
    away_score = match_data.get("away_score", 0)
    
    # Convert to int if they're strings
    try:
        home_score = int(home_score) if home_score is not None else 0
        away_score = int(away_score) if away_score is not None else 0
    except (ValueError, TypeError):
        return False
    
    return home_score == 0 and away_score == 0

def get_match_key(match_data):
    """Generate unique key for match to prevent duplicates"""
    # Use match_id + over/under lines to create unique identifier
    match_id = match_data.get("match_id", "unknown")
    over_under = match_data.get("over_under", {})
    
    # Create key based on match and qualifying O/U lines
    ou_lines = []
    if over_under and isinstance(over_under, dict):
        for line_key, line_data in over_under.items():
            if isinstance(line_data, dict):
                line_value = line_data.get("line")
                if line_value and line_value >= 3.0:
                    ou_lines.append(str(line_value))
    
    ou_signature = "|".join(sorted(ou_lines))
    return f"{match_id}_{ou_signature}_halftime"

def load_config():
    """Load configuration from ou_3_no_score.json"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"OU3 No Score Alert: Error loading config: {e}")
        return {
            "enabled": True,
            "criteria": {"min_ou_line": 3.0, "required_status": "half_time"}
        }

def get_status_description(status_id):
    """Get status description from ID (corrected mapping)"""
    status_map = {
        1: "Not started",
        2: "First half",
        3: "Half-time break",
        4: "Second half",
        5: "Extra time",
        6: "Penalty shootout",
        7: "Finished",
        8: "Finished",
        9: "Postponed",
        10: "Canceled",
        11: "To be announced",
        12: "Interrupted",
        13: "Abandoned",
        14: "Suspended"
    }
    return status_map.get(status_id, f"Unknown Status ({status_id})")

def write_alert_header(alert_count, matching_matches, total_scanned):
    """Write header for OU3 No Score alert log (styled like step6)"""
    current_time = get_eastern_time()
    
    log_and_print("\n" + "="*80)
    log_and_print(f"OU 3.0+ SCORELESS HALF TIME ALERT CYCLE - 0-0 HALF-TIME ONLY".center(80))
    log_and_print(f"Alert Time: {current_time}".center(80))
    log_and_print(f"NEW Half-time Matches Found: {matching_matches} of {total_scanned} scanned".center(80))
    log_and_print("="*80)

def format_ou_match(match, daily_alert_number):
    """Format match details (same style as step6) with daily running count"""
    log_and_print("\n" + "="*80)
    log_and_print(f"OU 3.0+ SCORELESS HALF TIME ALERT #{daily_alert_number}".center(80))
    log_and_print(f"Found: {get_eastern_time()}".center(80))
    log_and_print(f"Match ID: {match.get('match_id', 'N/A')}".center(80))
    log_and_print(f"Competition ID: {match.get('competition_id', 'N/A')}".center(80))
    log_and_print("="*80)
    log_and_print("")
    
    log_and_print(f"Competition: {match.get('competition')} ({match.get('country')})")
    log_and_print(f"Match: {match.get('home_team')} vs {match.get('away_team')}")
    
    # Score
    score = match.get("score", "N/A")
    log_and_print(f"Score: {score}")
    
    # Status with ID (should always be Half-time break for this alert)
    status_id = match.get("status_id")
    if status_id is not None:
        status_description = get_status_description(status_id)
        status = f"{status_description} (ID: {status_id})"
    else:
        status = match.get("status", "Unknown")
    log_and_print(f"Status: {status}")
    
    # Complete Betting Odds (same format as step6)
    log_and_print("\n--- MATCH BETTING ODDS ---")
    
    # Prepare formatted odds display
    has_any_odds = False
    
    # Money Line (Full Time Result)
    ftr = match.get("full_time_result", {})
    if ftr and isinstance(ftr, dict):
        home_odds = ftr.get("home", "N/A")
        draw_odds = ftr.get("draw", "N/A")
        away_odds = ftr.get("away", "N/A")
        ftr_time = ftr.get("time", "N/A")
        
        if any(odds != "N/A" for odds in [home_odds, draw_odds, away_odds]):
            log_and_print(f"│ ML:     │ Home: {home_odds:<4} │ Draw: {draw_odds:<5} │ Away: {away_odds:<5} │ (@{ftr_time}')")
            has_any_odds = True
    
    # Spread
    spread = match.get("spread", {})
    if spread and isinstance(spread, dict):
        home_odds = spread.get("home", "N/A")
        away_odds = spread.get("away", "N/A")
        handicap = spread.get("handicap", "N/A")
        spread_time = spread.get("time", "N/A")
        
        if any(odds != "N/A" for odds in [home_odds, away_odds]):
            log_and_print(f"│ Spread: │ Home: {home_odds:<4} │ Hcap: {handicap:<5} │ Away: {away_odds:<5} │ (@{spread_time}')")
            has_any_odds = True
    
    # Over/Under (all lines, highlighting 3.0+)
    over_under = match.get("over_under", {})
    if over_under and isinstance(over_under, dict):
        # Sort lines by value for consistent display
        sorted_lines = []
        for line_key, line_data in over_under.items():
            if isinstance(line_data, dict):
                line_value = line_data.get("line")
                if line_value is not None:
                    sorted_lines.append((line_value, line_data))
        
        sorted_lines.sort(key=lambda x: x[0])  # Sort by line value
        
        for line_value, line_data in sorted_lines:
            over_odds = line_data.get("over", "N/A")
            under_odds = line_data.get("under", "N/A")
            ou_time = line_data.get("time", "N/A")
            
            # Highlight qualifying lines (3.0+) but show all
            qualifier = " ★" if line_value >= 3.0 else ""
            log_and_print(f"│ O/U:    │ Over: {over_odds:<4} │ Line: {line_value:<5} │ Under: {under_odds:<4} │ (@{ou_time}'){qualifier}")
            has_any_odds = True
    
    if not has_any_odds:
        log_and_print("No betting odds available")
    
    # Complete Environment (same as step6)
    log_and_print("\n--- MATCH ENVIRONMENT ---")
    env_summary = match.get("environment_summary", [])
    environment = match.get("environment", {})
    
    if env_summary:
        # Check if we need to add Weather field (it's often missing from environment_summary)
        weather = environment.get("weather_description") if environment else None
        if weather:
            log_and_print(f"Weather: {weather}")
        
        # Then show the existing environment summary
        for env_line in env_summary:
            log_and_print(env_line)
    else:
        # Build environment display from individual fields (fallback)
        if environment:
            # Weather first
            weather = environment.get("weather_description", "Unknown")
            log_and_print(f"Weather: {weather}")
            
            # Temperature 
            temp = environment.get("temperature", "None")
            log_and_print(f"Temperature: {temp}")
            
            # Wind
            wind_desc = environment.get("wind_description", "Calm")
            wind_val = environment.get("wind_value", "None")
            wind_unit = environment.get("wind_unit", "None")
            log_and_print(f"Wind: {wind_desc}, {wind_val} {wind_unit}")
        else:
            log_and_print("No environment data available")

def check_ou_3_no_score_alert():
    """Main function to check for OU 3.0+ matches at HALF-TIME BREAK ONLY (fresh fetch only, no duplicates)"""
    print("OU3 No Score Alert: Starting over/under 3.0+ HALF-TIME BREAK monitoring...")
    
    # Setup logging
    global logger
    logger = setup_logging()
    
    # Load config
    config = load_config()
    if not config.get("enabled", True):
        print("OU3 No Score Alert: Alert disabled in config")
        return []
    
    min_line = config.get("criteria", {}).get("min_ou_line", 3.0)
    
    # Load step5 data
    if not STEP5_JSON.exists():
        print("OU3 No Score Alert: Error - step5.json not found")
        return []
        
    try:
        with open(STEP5_JSON, 'r') as f:
            step5_data = json.load(f)
    except Exception as e:
        print(f"OU3 No Score Alert: Error loading step5.json: {e}")
        return []
    
    # Get ONLY the latest/freshest data (no history)
    if "history" in step5_data and step5_data["history"]:
        latest_data = step5_data["history"][-1]  # Only the most recent fetch
        matches = latest_data.get("matches", {})
        current_fetch_time = latest_data.get("generated_at", "Unknown")
    else:
        matches = step5_data.get("matches", {})
        current_fetch_time = step5_data.get("generated_at", "Unknown")
    
    # Load previously processed matches and last fetch time
    processed_matches, last_fetch_time = load_processed_matches()
    
    # Check if this is a new fetch
    if current_fetch_time == last_fetch_time:
        print(f"OU3 No Score Alert: Same fetch time as last run ({current_fetch_time}) - skipping to avoid duplicates")
        return []
    
    print(f"OU3 No Score Alert: New fetch detected - {current_fetch_time}")
    print(f"OU3 No Score Alert: Last processed fetch was - {last_fetch_time}")
    
    total_matches = len(matches)
    matching_matches = []
    skipped_matches = 0
    non_half_time_matches = 0
    
    print(f"OU3 No Score Alert: Scanning {total_matches} matches for:")
    print(f"  1. O/U lines >= {min_line}")
    print(f"  2. Half-time break status (ID=3)")
    print(f"  3. Scoreless at half-time (0-0)")
    
    # Scan for qualifying matches
    for match_id, match_data in matches.items():
        # First check: Is match at half time?
        if not is_half_time_match(match_data):
            non_half_time_matches += 1
            continue
            
        # Second check: Is the game scoreless (0-0)?
        if not is_scoreless_at_halftime(match_data):
            continue
            
        # Third check: Does it have qualifying O/U lines?
        over_under = match_data.get("over_under", {})
        has_qualifying_line = False
        
        if over_under and isinstance(over_under, dict):
            for line_key, line_data in over_under.items():
                if isinstance(line_data, dict):
                    line_value = line_data.get("line")
                    if line_value and line_value >= min_line:
                        has_qualifying_line = True
                        break
        
        if not has_qualifying_line:
            continue
            
        # Fourth check: Have we already processed this match?
        match_key = get_match_key(match_data)
        if match_key in processed_matches:
            skipped_matches += 1
            print(f"OU3 No Score Alert: Skipping duplicate - {match_data.get('home_team')} vs {match_data.get('away_team')}")
            continue
        
        # Match qualifies - add to results and mark as processed
        matching_matches.append(match_data)
        processed_matches.add(match_key)
    
    num_found = len(matching_matches)
    print(f"OU3 No Score Alert: Found {num_found} NEW scoreless half-time matches with O/U lines >= {min_line}")
    print(f"OU3 No Score Alert: Skipped {skipped_matches} duplicates, {non_half_time_matches} non-half-time-break matches")
    
    if num_found > 0:
        # Get current daily count
        current_count, today = get_and_increment_daily_count()
        
        # Generate alert cycle number (simple increment based on time)
        alert_count = int(datetime.now(TZ).timestamp()) % 10000
        
        # Write header
        write_alert_header(alert_count, num_found, total_matches)
        
        # Process each qualifying match with daily running count
        for i, match in enumerate(matching_matches, 1):
            current_count += 1  # Increment for each match
            format_ou_match(match, current_count)
            
            # Add separator between matches
            if i < num_found:
                log_and_print("\n" + "-"*80)
        
        # Save the updated daily count
        save_daily_count(current_count, today)
        
        # Flush log
        for handler in logger.handlers:
            handler.flush()
    
    # Save updated processed matches list with current fetch time
    save_processed_matches(processed_matches, current_fetch_time)
    
    return matching_matches

if __name__ == "__main__":
    # Test the alert independently
    matches = check_ou_3_no_score_alert()
    print(f"OU3 No Score Alert completed: {len(matches)} qualifying half-time break matches found")
