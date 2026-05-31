# ============================================
# EXPERT RULES ENGINE
# Tourist Place Recommendation System
# ============================================

# ============================================
# SCORING WEIGHTS (Total = 100 when normalized)
# ============================================
WEIGHTS = {
    'budget':           15,
    'season':           12,
    'interests':        20,
    'region':            8,
    'terrain':           6,
    'activity_level':    7,
    'travel_type':       6,
    'trip_purpose':      5,
    'duration':          4,
    'crowd':             5,
    'age_group':         4,
    'food':              3,
    'accommodation':     2,
    'experience_type':   3,
    'weather_pref':      2,
    'safety':            2,
    'connectivity':      2,
    'accessibility':     2,
    'eco_friendly':      1,
}

# ============================================
# HARD RULES (Forward Chaining - Applied First)
# These filter OUT or BOOST destinations before scoring
# ============================================

def apply_hard_rules(destinations, user_input):
    """Apply forward chaining hard rules to filter/warn/boost destinations."""
    filtered = []
    warnings = []
    boosts = {}

    for dest in destinations:
        include = True
        boost = 0

        # ---- HARD RULE 1: High Altitude Health ----
        if user_input.get('health') == 'avoid_high_altitude':
            if dest['altitude_meters'] and int(dest['altitude_meters']) > 2500:
                include = False
                continue

        # ---- HARD RULE 2: Wheelchair Accessibility ----
        if user_input.get('accessibility') == 'Wheelchair':
            if dest['accessibility'] not in ('Accessible',):
                include = False
                continue

        # ---- HARD RULE 3: Budget vs Luxury Mismatch ----
        if user_input.get('budget') == 'Low' and user_input.get('accommodation') == 'Luxury':
            if dest['budget_category'] == 'Low':
                warnings.append("Luxury accommodation may exceed your budget range. Consider mid-range options.")

        # ---- HARD RULE 4: Desert Summer Warning ----
        if user_input.get('season') == 'Summer' and 'Desert' in dest.get('terrain', ''):
            warnings.append(f"{dest['place_name']}: Extreme heat expected in summer (45°C+). Plan accordingly.")

        # ---- HARD RULE 5: Honeymoon Boost ----
        if user_input.get('trip_purpose') == 'Honeymoon':
            if dest.get('is_romantic'):
                boost += 15
            romantic_places = ['Udaipur', 'Andaman', 'Munnar', 'Coorg', 'Goa',
                                'Alleppey', 'Varkala', 'Kovalam', 'Darjeeling',
                                'Gangtok', 'Mahabaleshwar', 'Pondicherry']
            if dest['place_name'] in romantic_places:
                boost += 10

        # ---- HARD RULE 6: Senior + Challenging Activity Warning ----
        if user_input.get('age_group') == 'Senior' and user_input.get('activity_level') == 'Challenging':
            warnings.append("Challenging activities may not be suitable for senior travelers. Showing moderate alternatives too.")
            if dest['activity_level'] == 'Challenging' and 'Senior' not in dest.get('age_group', ''):
                boost -= 20

        # ---- HARD RULE 7: Offbeat Filter ----
        if user_input.get('crowd') == 'Offbeat':
            if dest['crowd_level'] == 'Popular':
                boost -= 15

        # ---- HARD RULE 8: Family + Kids Boost ----
        if user_input.get('travel_type') == 'Family':
            if dest.get('is_family_fav'):
                boost += 10
            if 'Kids' in dest.get('age_group', ''):
                boost += 8

        # ---- HARD RULE 9: Wildlife Season Warning ----
        if user_input.get('interests') and 'Wildlife' in user_input.get('interests', []):
            safari_places = ['Ranthambore', 'Jim Corbett', 'Kaziranga', 'Bandhavgarh', 'Gir']
            if dest['place_name'] in safari_places:
                if user_input.get('season') == 'Monsoon':
                    warnings.append(f"{dest['place_name']}: Wildlife parks may be closed during monsoon season (Jun-Sep).")
                    boost -= 20

        # ---- HARD RULE 10: Poor Connectivity Filter ----
        if user_input.get('connectivity') == 'Good Internet Required':
            if dest['connectivity'] == 'Poor':
                include = False
                continue

        # ---- HARD RULE 11: Solo Female Safety ----
        if user_input.get('travel_type') == 'Solo' and user_input.get('age_group') == 'YoungAdults':
            if dest['safety_level'] == 'High':
                boost += 5

        # ---- HARD RULE 12: Backpacker Boost ----
        if user_input.get('experience_type') == 'Backpacking':
            if dest.get('is_backpacker'):
                boost += 12
            if dest['budget_category'] == 'Low':
                boost += 8

        # ---- HARD RULE 13: Photography Purpose Boost ----
        if user_input.get('trip_purpose') == 'Photography':
            photo_places = ['Hampi', 'Jaisalmer', 'Varanasi', 'Leh-Ladakh',
                            'Spiti Valley', 'Cherrapunji', 'Rann of Kutch',
                            'Tawang', 'Ziro Valley']
            if dest['place_name'] in photo_places:
                boost += 12

        # ---- HARD RULE 14: Pilgrimage Filter ----
        if user_input.get('trip_purpose') == 'Pilgrimage':
            spiritual_tags = ['Spiritual', 'Religious', 'Buddhist', 'Hindu']
            if any(tag in dest.get('tags', '') for tag in spiritual_tags):
                boost += 15

        # ---- HARD RULE 15: Eco-Friendly Filter ----
        if user_input.get('eco_preference') == 'Eco-Friendly':
            if dest.get('eco_friendly'):
                boost += 10
            else:
                boost -= 5

        if include:
            boosts[dest['id']] = boost
            filtered.append(dest)

    return filtered, list(set(warnings)), boosts


# ============================================
# SCORING ALGORITHM (MCDM - Multi-Criteria)
# ============================================

def calculate_match_score(destination, user_input, boost=0):
    """Calculate match percentage for a destination based on user preferences."""
    score = 0
    max_score = 0

    # ---- 1. BUDGET MATCH (Weight: 15) ----
    if user_input.get('budget'):
        max_score += WEIGHTS['budget']
        budget_map = {'Low': ['Low'], 'Medium': ['Low', 'Medium'], 'High': ['Low', 'Medium', 'High']}
        if destination['budget_category'] in budget_map.get(user_input['budget'], []):
            score += WEIGHTS['budget']

    # ---- 2. SEASON MATCH (Weight: 12) ----
    if user_input.get('season'):
        max_score += WEIGHTS['season']
        dest_seasons = [s.strip() for s in destination['best_season'].split(',')]
        if user_input['season'] in dest_seasons or 'All' in dest_seasons:
            score += WEIGHTS['season']
        elif user_input.get('month'):
            dest_months = [m.strip() for m in destination['best_months'].split(',')]
            if user_input['month'] in dest_months:
                score += WEIGHTS['season'] * 0.8

    # ---- 3. INTERESTS / TAGS MATCH (Weight: 20) ----
    if user_input.get('interests'):
        max_score += WEIGHTS['interests']
        dest_tags = [t.strip().lower() for t in destination['tags'].split(',')]
        user_interests = [i.strip().lower() for i in user_input['interests']]
        matched = sum(1 for i in user_interests if i in dest_tags)
        if len(user_interests) > 0:
            score += (matched / len(user_interests)) * WEIGHTS['interests']

    # ---- 4. REGION MATCH (Weight: 8) ----
    if user_input.get('region'):
        max_score += WEIGHTS['region']
        if destination['region'] == user_input['region']:
            score += WEIGHTS['region']

    # ---- 5. TERRAIN MATCH (Weight: 6) ----
    if user_input.get('terrain'):
        max_score += WEIGHTS['terrain']
        dest_terrains = [t.strip() for t in destination['terrain'].split(',')]
        if user_input['terrain'] in dest_terrains:
            score += WEIGHTS['terrain']

    # ---- 6. ACTIVITY LEVEL MATCH (Weight: 7) ----
    if user_input.get('activity_level'):
        max_score += WEIGHTS['activity_level']
        if destination['activity_level'] == user_input['activity_level']:
            score += WEIGHTS['activity_level']
        elif (user_input['activity_level'] == 'Moderate' and
              destination['activity_level'] in ['Easy', 'Moderate']):
            score += WEIGHTS['activity_level'] * 0.5

    # ---- 7. TRAVEL TYPE MATCH (Weight: 6) ----
    if user_input.get('travel_type'):
        max_score += WEIGHTS['travel_type']
        dest_types = [t.strip() for t in destination['travel_type'].split(',')]
        if user_input['travel_type'] in dest_types:
            score += WEIGHTS['travel_type']

    # ---- 8. TRIP PURPOSE MATCH (Weight: 5) ----
    if user_input.get('trip_purpose'):
        max_score += WEIGHTS['trip_purpose']
        dest_purposes = [p.strip() for p in destination['trip_purpose'].split(',')]
        if user_input['trip_purpose'] in dest_purposes:
            score += WEIGHTS['trip_purpose']

    # ---- 9. TRIP DURATION MATCH (Weight: 4) ----
    if user_input.get('duration'):
        max_score += WEIGHTS['duration']
        dest_durations = [d.strip() for d in destination['trip_duration'].split(',')]
        if user_input['duration'] in dest_durations:
            score += WEIGHTS['duration']

    # ---- 10. CROWD PREFERENCE MATCH (Weight: 5) ----
    if user_input.get('crowd'):
        max_score += WEIGHTS['crowd']
        if (destination['crowd_level'] == user_input['crowd'] or
                destination['crowd_level'] == 'Both'):
            score += WEIGHTS['crowd']

    # ---- 11. AGE GROUP MATCH (Weight: 4) ----
    if user_input.get('age_group'):
        max_score += WEIGHTS['age_group']
        dest_ages = [a.strip() for a in destination['age_group'].split(',')]
        if user_input['age_group'] in dest_ages:
            score += WEIGHTS['age_group']

    # ---- 12. FOOD PREFERENCE MATCH (Weight: 3) ----
    if user_input.get('food'):
        max_score += WEIGHTS['food']
        dest_food = [f.strip().lower() for f in destination['food_options'].split(',')]
        if user_input['food'].lower() in dest_food:
            score += WEIGHTS['food']

    # ---- 13. ACCOMMODATION MATCH (Weight: 2) ----
    if user_input.get('accommodation'):
        max_score += WEIGHTS['accommodation']
        dest_acc = [a.strip() for a in destination['accommodation'].split(',')]
        if user_input['accommodation'] in dest_acc:
            score += WEIGHTS['accommodation']

    # ---- 14. EXPERIENCE TYPE MATCH (Weight: 3) ----
    if user_input.get('experience_type'):
        max_score += WEIGHTS['experience_type']
        dest_exp = [e.strip() for e in destination['experience_type'].split(',')]
        if user_input['experience_type'] in dest_exp:
            score += WEIGHTS['experience_type']

    # ---- 15. WEATHER PREFERENCE MATCH (Weight: 2) ----
    if user_input.get('weather_pref'):
        max_score += WEIGHTS['weather_pref']
        if (destination['weather_type'] == user_input['weather_pref'] or
                destination['weather_type'] == 'Any'):
            score += WEIGHTS['weather_pref']

    # ---- 16. SAFETY LEVEL MATCH (Weight: 2) ----
    if user_input.get('safety'):
        max_score += WEIGHTS['safety']
        if destination['safety_level'] == user_input['safety']:
            score += WEIGHTS['safety']

    # ---- 17. CONNECTIVITY MATCH (Weight: 2) ----
    if user_input.get('connectivity'):
        max_score += WEIGHTS['connectivity']
        conn_map = {'Good': ['Good'], 'Moderate': ['Good', 'Moderate'], 'Poor': ['Good', 'Moderate', 'Poor']}
        if destination['connectivity'] in conn_map.get(user_input['connectivity'], []):
            score += WEIGHTS['connectivity']

    # ---- 18. ECO-FRIENDLY MATCH (Weight: 1) ----
    if user_input.get('eco_preference') == 'Eco-Friendly':
        max_score += WEIGHTS['eco_friendly']
        if destination.get('eco_friendly'):
            score += WEIGHTS['eco_friendly']

    # ---- CALCULATE FINAL PERCENTAGE ----
    if max_score == 0:
        base_pct = 75  # No filters = show all with 75% base
    else:
        base_pct = round((score / max_score) * 100)

    # Add boost from hard rules
    final_pct = min(100, base_pct + boost)
    final_pct = max(0, final_pct)

    return final_pct


# ============================================
# SMART SUGGESTION (Fallback if 0 results)
# ============================================

def get_smart_suggestions(destinations, user_input):
    """Relax one filter at a time to find partial matches."""
    relaxed_input = user_input.copy()
    suggestions = []

    # Try relaxing each filter one by one
    relaxable_keys = ['season', 'budget', 'region', 'activity_level', 'crowd']

    for key in relaxable_keys:
        if relaxed_input.get(key):
            temp_input = relaxed_input.copy()
            temp_input.pop(key)

            for dest in destinations:
                score = calculate_match_score(dest, temp_input)
                if score >= 50:
                    dest_copy = dict(dest)
                    dest_copy['match_score'] = score
                    dest_copy['relaxed_filter'] = key
                    suggestions.append(dest_copy)

            if suggestions:
                suggestions.sort(key=lambda x: x['match_score'], reverse=True)
                return suggestions[:6], f"No exact matches. Showing results by relaxing '{key}' filter."

    return [], "No suggestions found. Try fewer filters."


# ============================================
# TRENDING / BADGE LOGIC
# ============================================

def assign_badges(destinations):
    """Assign display badges to destinations."""
    for dest in destinations:
        badges = []
        if dest.get('is_trending'):
            badges.append({'label': '🔥 Trending', 'class': 'badge-trending'})
        if dest.get('is_hidden_gem'):
            badges.append({'label': '💎 Hidden Gem', 'class': 'badge-gem'})
        if dest.get('is_family_fav'):
            badges.append({'label': '👨‍👩‍👧 Family Fav', 'class': 'badge-family'})
        if dest.get('is_romantic'):
            badges.append({'label': '💑 Romantic', 'class': 'badge-romantic'})
        if dest.get('is_backpacker'):
            badges.append({'label': '🎒 Backpacker Pick', 'class': 'badge-backpacker'})
        dest['badges'] = badges
    return destinations
