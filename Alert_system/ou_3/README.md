# OU 3.0+ Alert System - Technical Documentation

## Overview

The OU 3.0+ Alert System serves as the **foundational template** for all independent alert modules in the Football Bot pipeline. This system demonstrates the complete architecture, scanning methodology, triggering logic, and output formatting that should be replicated across all future alert implementations.

## Alert Architecture Foundation

### Core Design Principles

1. **Complete Independence**: Each alert is a standalone module with no dependencies on other alerts or main pipeline modifications
2. **Plug-and-Play**: Can be added or removed without touching existing code
3. **Fresh Data Only**: Only processes the latest pipeline fetch to avoid stale alerts
4. **Duplicate Prevention**: Tracks processed matches to prevent repeat alerts
5. **Live Match Focus**: Only alerts on active/live matches
6. **Standardized Output**: Consistent logging format across all alert types

### Directory Structure (STANDARD)
```
Alert_system/
├── ou_3/                           # Alert module directory
│   ├── ou_3.py                     # Main alert logic
│   ├── ou_3.json                   # Configuration file
│   ├── ou_3.log                    # Dedicated alert log
│   ├── processed_matches.json      # Duplicate tracking
│   ├── daily_alert_count.json     # Daily counter
│   └── README.md                   # This documentation
```

## Data Source & Scanning Logic

### Source Location
```python
STEP5_JSON = Path("/root/CascadeProjects/Football_bot/step5/step5.json")
```

### Fresh Fetch Detection (STANDARD)
```python
# Get ONLY the latest/freshest data (no history)
if "history" in step5_data and step5_data["history"]:
    latest_data = step5_data["history"][-1]  # Only the most recent fetch
    matches = latest_data.get("matches", {})
    current_fetch_time = latest_data.get("generated_at", "Unknown")
else:
    matches = step5_data.get("matches", {})
    current_fetch_time = step5_data.get("generated_at", "Unknown")

# Check if this is a new fetch
if current_fetch_time == last_fetch_time:
    print(f"OU3 Alert: Same fetch time as last run ({current_fetch_time}) - skipping to avoid duplicates")
    return []
```

### Live Match Filtering (STANDARD)
```python
# Live match status IDs
LIVE_STATUS_IDS = {1, 2, 3}  # First Half, Half Time, Second Half

def is_live_match(match_data):
    """Check if match is live (First Half, Half Time, Second Half)"""
    status_id = match_data.get("status_id")
    return status_id in LIVE_STATUS_IDS
```

## Trigger Logic Framework

### Three-Stage Filtering Process (STANDARD)

1. **Live Match Check**: Only process matches with status IDs 1, 2, or 3
2. **Criteria Check**: Apply alert-specific conditions (OU lines ≥ 3.0)
3. **Duplicate Check**: Ensure match hasn't been processed before

```python
for match_id, match_data in matches.items():
    # Stage 1: Is match live?
    if not is_live_match(match_data):
        non_live_matches += 1
        continue
        
    # Stage 2: Does it meet alert criteria? (CUSTOMIZABLE PER ALERT)
    over_under = match_data.get("over_under", {})
    has_qualifying_line = False
    
    if over_under and isinstance(over_under, dict):
        for line_key, line_data in over_under.items():
            if isinstance(line_data, dict):
                line_value = line_data.get("line")
                if line_value and line_value >= min_line:  # ALERT-SPECIFIC CRITERIA
                    has_qualifying_line = True
                    break
    
    if not has_qualifying_line:
        continue
        
    # Stage 3: Have we already processed this match?
    match_key = get_match_key(match_data)
    if match_key in processed_matches:
        skipped_matches += 1
        continue
    
    # Match qualifies - add to results and mark as processed
    matching_matches.append(match_data)
    processed_matches.add(match_key)
```

## Duplicate Prevention System (STANDARD)

### Match Key Generation
```python
def get_match_key(match_data):
    """Generate unique key for match to prevent duplicates"""
    match_id = match_data.get("match_id", "unknown")
    # Include alert-specific data in key for precision
    # For OU3: Include qualifying O/U lines
    over_under = match_data.get("over_under", {})
    
    ou_lines = []
    if over_under and isinstance(over_under, dict):
        for line_key, line_data in over_under.items():
            if isinstance(line_data, dict):
                line_value = line_data.get("line")
                if line_value and line_value >= 3.0:  # ALERT-SPECIFIC THRESHOLD
                    ou_lines.append(str(line_value))
    
    ou_signature = "|".join(sorted(ou_lines))
    return f"{match_id}_{ou_signature}"
```

### Persistent Tracking
```python
def load_processed_matches():
    """Load the list of matches we've already processed"""
    try:
        with open(PROCESSED_MATCHES_FILE, 'r') as f:
            data = json.load(f)
            processed_list = data.get("processed_matches", [])
            return set(processed_list), data.get("last_fetch_time", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return set(), ""

def save_processed_matches(processed_matches, fetch_time):
    """Save the list of processed matches and fetch time"""
    data = {
        "processed_matches": list(processed_matches),
        "last_fetch_time": fetch_time,
        "last_updated": get_eastern_time()
    }
    with open(PROCESSED_MATCHES_FILE, 'w') as f:
        json.dump(data, f, indent=2)
```

## Daily Counter System (STANDARD)

### Implementation
```python
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
    data = {"date": date, "count": count, "last_updated": get_eastern_time()}
    with open(DAILY_COUNTER_FILE, 'w') as f:
        json.dump(data, f, indent=2)
```

### Usage in Main Loop
```python
if num_found > 0:
    # Get current daily count
    current_count, today = get_and_increment_daily_count()
    
    # Process each qualifying match with daily running count
    for i, match in enumerate(matching_matches, 1):
        current_count += 1  # Increment for each match
        format_ou_match(match, current_count)
        
        if i < num_found:
            log_and_print("\n" + "-"*80)
    
    # Save the updated daily count
    save_daily_count(current_count, today)
```

## Standard Output Format

### Time Zone Configuration (STANDARD)
```python
from zoneinfo import ZoneInfo
TZ = ZoneInfo("America/New_York")  # Eastern timezone

def get_eastern_time():
    """Get current Eastern time formatted string"""
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")
```

### Logging Setup (STANDARD)
```python
def setup_logging():
    """Setup logging that writes to alert log file"""
    logger = logging.getLogger("OU3_Alert")  # Use alert-specific name
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    
    # Simple format (no timestamp prefix since we add our own)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

def log_and_print(message):
    """Log message to file and print to console"""
    logger.info(message)
    print(message)
```

### Header Format (STANDARD)
```python
def write_alert_header(alert_count, matching_matches, total_scanned):
    """Write header for alert log"""
    current_time = get_eastern_time()
    
    log_and_print("\n" + "="*80)
    log_and_print(f"OU 3.0+ ALERT CYCLE - LIVE MATCHES ONLY".center(80))  # CUSTOMIZE ALERT NAME
    log_and_print(f"Alert Time: {current_time}".center(80))
    log_and_print(f"NEW Matches Found: {matching_matches} of {total_scanned} scanned".center(80))
    log_and_print("="*80)
```

### Individual Match Format (STANDARD)
```python
def format_ou_match(match, daily_alert_number):
    """Format match details with daily running count"""
    log_and_print("\n" + "="*80)
    log_and_print(f"OU 3.0+ ALERT #{daily_alert_number}".center(80))  # CUSTOMIZE ALERT NAME
    log_and_print(f"Found: {get_eastern_time()}".center(80))
    log_and_print(f"Match ID: {match.get('match_id', 'N/A')}".center(80))
    log_and_print(f"Competition ID: {match.get('competition_id', 'N/A')}".center(80))
    log_and_print("="*80)
    log_and_print("")
    
    # Basic Match Info
    log_and_print(f"Competition: {match.get('competition')} ({match.get('country')})")
    log_and_print(f"Match: {match.get('home_team')} vs {match.get('away_team')}")
    log_and_print(f"Score: {match.get('score', 'N/A')}")
    
    # Status with ID
    status_id = match.get("status_id")
    if status_id is not None:
        status_description = get_status_description(status_id)
        status = f"{status_description} (ID: {status_id})"
    else:
        status = match.get("status", "Unknown")
    log_and_print(f"Status: {status}")
    
    # Complete Betting Odds Section
    log_and_print("\n--- MATCH BETTING ODDS ---")
    
    # Money Line (Full Time Result)
    ftr = match.get("full_time_result", {})
    if ftr and isinstance(ftr, dict):
        home_odds = ftr.get("home", "N/A")
        draw_odds = ftr.get("draw", "N/A")
        away_odds = ftr.get("away", "N/A")
        ftr_time = ftr.get("time", "N/A")
        
        if any(odds != "N/A" for odds in [home_odds, draw_odds, away_odds]):
            log_and_print(f"│ ML:     │ Home: {home_odds:<4} │ Draw: {draw_odds:<5} │ Away: {away_odds:<5} │ (@{ftr_time}')")
    
    # Spread
    spread = match.get("spread", {})
    if spread and isinstance(spread, dict):
        home_odds = spread.get("home", "N/A")
        away_odds = spread.get("away", "N/A")
        handicap = spread.get("handicap", "N/A")
        spread_time = spread.get("time", "N/A")
        
        if any(odds != "N/A" for odds in [home_odds, away_odds]):
            log_and_print(f"│ Spread: │ Home: {home_odds:<4} │ Hcap: {handicap:<5} │ Away: {away_odds:<5} │ (@{spread_time}')")
    
    # Over/Under (with qualifying line highlighting)
    over_under = match.get("over_under", {})
    if over_under and isinstance(over_under, dict):
        sorted_lines = []
        for line_key, line_data in over_under.items():
            if isinstance(line_data, dict):
                line_value = line_data.get("line")
                if line_value is not None:
                    sorted_lines.append((line_value, line_data))
        
        sorted_lines.sort(key=lambda x: x[0])
        
        for line_value, line_data in sorted_lines:
            over_odds = line_data.get("over", "N/A")
            under_odds = line_data.get("under", "N/A")
            ou_time = line_data.get("time", "N/A")
            
            # Highlight qualifying lines (CUSTOMIZE CRITERIA)
            qualifier = " ★" if line_value >= 3.0 else ""
            log_and_print(f"│ O/U:    │ Over: {over_odds:<4} │ Line: {line_value:<5} │ Under: {under_odds:<4} │ (@{ou_time}'){qualifier}")
    
    # Complete Environment Section
    log_and_print("\n--- MATCH ENVIRONMENT ---")
    env_summary = match.get("environment_summary", [])
    environment = match.get("environment", {})
    
    if env_summary:
        # Add Weather field if missing
        weather = environment.get("weather_description") if environment else None
        if weather:
            log_and_print(f"Weather: {weather}")
        
        for env_line in env_summary:
            log_and_print(env_line)
    else:
        # Build environment display from individual fields
        if environment:
            weather = environment.get("weather_description", "Unknown")
            log_and_print(f"Weather: {weather}")
            
            temp = environment.get("temperature", "None")
            log_and_print(f"Temperature: {temp}")
            
            wind_desc = environment.get("wind_description", "Calm")
            wind_val = environment.get("wind_value", "None")
            wind_unit = environment.get("wind_unit", "None")
            log_and_print(f"Wind: {wind_desc}, {wind_val} {wind_unit}")
        else:
            log_and_print("No environment data available")
```

### Status Description Mapping (STANDARD)
```python
def get_status_description(status_id):
    """Get status description from ID"""
    status_map = {
        0: "Not Started",
        1: "First Half", 
        2: "Half Time",
        3: "Second Half",
        4: "Extra Time",
        5: "Penalty Shootout",
        6: "Full Time",
        7: "Cancelled",
        8: "Suspended",
        9: "Postponed",
        10: "To Be Determined",
        11: "Delayed",
        12: "Abandoned"
    }
    return status_map.get(status_id, f"Unknown Status ({status_id})")
```

## Configuration System (STANDARD)

### Config File Structure (`alert_name.json`)
```json
{
  "enabled": true,
  "criteria": {
    "min_ou_line": 3.0
  },
  "description": "Over/Under 3.0+ Line Alert",
  "alert_type": "ou_3"
}
```

### Config Loading (STANDARD)
```python
def load_config():
    """Load configuration from alert config file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Alert: Error loading config: {e}")
        return {
            "enabled": True,
            "criteria": {"min_ou_line": 3.0}  # DEFAULT CRITERIA
        }
```

## File Naming Conventions (STANDARD)

- **Main Script**: `{alert_name}.py`
- **Config File**: `{alert_name}.json`
- **Log File**: `{alert_name}.log`
- **Processed Tracking**: `processed_matches.json`
- **Daily Counter**: `daily_alert_count.json`
- **Documentation**: `README.md`

## Integration Points

### Alert Manager Discovery
The alert will be automatically discovered by the Alert Manager when placed in the correct directory structure under `/root/CascadeProjects/Alert_system/`.

### Main Function Signature (STANDARD)
```python
def check_{alert_name}_alert():
    """Main function to check for {alert_type} matches"""
    # Returns list of qualifying matches
    return matching_matches

if __name__ == "__main__":
    # Test the alert independently
    matches = check_{alert_name}_alert()
    print(f"{alert_name} Alert completed: {len(matches)} qualifying matches found")
```

## Future Alert Development

### Steps to Create New Alert

1. **Copy OU3 Structure**: Use this directory as template
2. **Customize Criteria**: Modify the filtering logic in stage 2
3. **Update Match Key**: Adjust `get_match_key()` for alert-specific uniqueness
4. **Customize Output**: Change alert name in headers and logging
5. **Configure Thresholds**: Update config file with alert-specific criteria
6. **Test Independence**: Ensure alert runs standalone without dependencies

### Alert-Specific Customization Points

- **Filtering Criteria**: The condition logic in stage 2 of the filtering process
- **Match Key Generation**: Include relevant data points for duplicate detection
- **Alert Name**: Headers, log messages, and file names
- **Configuration**: Alert-specific thresholds and settings
- **Highlighting Logic**: Which betting lines or data to emphasize with ★

## Example Output

```
================================================================================
                        OU 3.0+ ALERT CYCLE - LIVE MATCHES ONLY                
                     Alert Time: 05/28/2025 11:05:23 PM EDT                     
                       NEW Matches Found: 1 of 23 scanned                       
================================================================================

================================================================================
                               OU 3.0+ ALERT #15                                
                       Found: 05/28/2025 11:05:23 PM EDT                        
                           Match ID: pxwrxlhyg538ryk                            
                        Competition ID: j1l4rjnhjg1m7vx                         
================================================================================

Competition: USA ULOC (United States)
Match: Monterey Bay FC vs Spokane Velocity
Score: 1 - 0 (HT: 1 - 0)
Status: Second Half (ID: 3)

--- MATCH BETTING ODDS ---
│ ML:     │ Home: -143 │ Draw: +274  │ Away: +347  │ (@6')
│ Spread: │ Home: -108 │ Hcap: -0.25 │ Away: -118  │ (@5')
│ O/U:    │ Over: -108 │ Line: 3.5   │ Under: -119 │ (@6') ★

--- MATCH ENVIRONMENT ---
Weather: Foggy
Temperature: 57.2°F
Wind: Light Breeze, 5.8 mph
```

This foundation ensures consistency, reliability, and scalability across all alert modules in the Football Bot ecosystem.
