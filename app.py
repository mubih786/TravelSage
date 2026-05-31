# ============================================
# TOURIST PLACE RECOMMENDATION SYSTEM
# Flask Application - app.py
# ============================================

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import uuid
import json
from database import (
    get_all_destinations, get_destination_by_id, get_trending_destinations,
    get_top_rated, get_hidden_gems, search_by_name, increment_view_count,
    add_to_wishlist, remove_from_wishlist, get_wishlist,
    save_search_history, get_search_history,
    add_review, get_reviews,
    add_to_compare, get_compare_list, clear_compare
)
from rules import apply_hard_rules, calculate_match_score, get_smart_suggestions, assign_badges

app = Flask(__name__)
app.secret_key = 'tourist_recommender_secret_key_2024'

# ============================================
# HELPER: Ensure session ID exists
# ============================================
def ensure_session():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

# ============================================
# ROUTE 1: HOME PAGE
# ============================================
@app.route('/')
def home():
    ensure_session()
    trending = get_trending_destinations(6)
    top_rated = get_top_rated(6)
    hidden_gems = get_hidden_gems(4)
    trending = assign_badges(trending)
    top_rated = assign_badges(top_rated)
    hidden_gems = assign_badges(hidden_gems)
    wishlist_ids = [w['id'] for w in get_wishlist(session['session_id'])]
    return render_template('index.html',
        trending=trending,
        top_rated=top_rated,
        hidden_gems=hidden_gems,
        wishlist_ids=wishlist_ids
    )

# ============================================
# ROUTE 2: SEARCH PAGE
# ============================================
@app.route('/search')
def search():
    ensure_session()
    return render_template('search.html')

# ============================================
# ROUTE 3: RESULTS PAGE
# ============================================
@app.route('/results', methods=['GET', 'POST'])
def results():
    ensure_session()
    sid = session['session_id']

    # Collect user input (all optional)
    user_input = {}
    fields = ['budget', 'season', 'month', 'region', 'terrain', 'activity_level',
              'travel_type', 'trip_purpose', 'duration', 'crowd', 'age_group',
              'food', 'accommodation', 'experience_type', 'weather_pref',
              'safety', 'connectivity', 'eco_preference', 'health', 'trip_style']

    for field in fields:
        val = request.form.get(field) or request.args.get(field)
        if val and val.strip():
            user_input[field] = val.strip()

    # Multi-select interests
    interests = request.form.getlist('interests') or request.args.getlist('interests')
    if interests:
        user_input['interests'] = interests

    # Sort & filter params
    sort_by = request.args.get('sort', 'match')
    filter_state = request.args.get('filter_state', '')

    # Get all destinations from DB
    all_destinations = get_all_destinations()

    # Apply Hard Rules (forward chaining)
    filtered_destinations, warnings, boosts = apply_hard_rules(all_destinations, user_input)

    # Apply state filter
    if filter_state:
        filtered_destinations = [d for d in filtered_destinations if d['state'] == filter_state]

    # Score each destination
    scored = []
    for dest in filtered_destinations:
        boost = boosts.get(dest['id'], 0)
        score = calculate_match_score(dest, user_input, boost)
        dest_copy = dict(dest)
        dest_copy['match_score'] = score
        scored.append(dest_copy)

    # Filter by minimum score if user gave any input
    if user_input:
        scored = [d for d in scored if d['match_score'] >= 30]

    # Smart suggestions if no results
    suggestions = []
    suggestion_msg = ''
    if not scored and user_input:
        suggestions, suggestion_msg = get_smart_suggestions(all_destinations, user_input)
        suggestions = assign_badges(suggestions)

    # Sort results
    if sort_by == 'rating':
        scored.sort(key=lambda x: x['rating'], reverse=True)
    elif sort_by == 'name':
        scored.sort(key=lambda x: x['place_name'])
    else:
        scored.sort(key=lambda x: x['match_score'], reverse=True)

    # Assign badges
    scored = assign_badges(scored)

    # Get unique states for filter dropdown
    all_states = sorted(set(d['state'] for d in all_destinations))

    # Save search to history
    save_search_history(sid, user_input, len(scored))

    # Get wishlist IDs for heart icons
    wishlist_ids = [w['id'] for w in get_wishlist(sid)]

    # Get compare list count
    compare_list = get_compare_list(sid)

    return render_template('results.html',
        results=scored,
        user_input=user_input,
        warnings=warnings,
        suggestions=suggestions,
        suggestion_msg=suggestion_msg,
        sort_by=sort_by,
        filter_state=filter_state,
        all_states=all_states,
        wishlist_ids=wishlist_ids,
        compare_list=compare_list,
        total=len(scored)
    )

# ============================================
# ROUTE 4: PLACE DETAIL PAGE
# ============================================
@app.route('/place/<int:dest_id>')
def place_detail(dest_id):
    ensure_session()
    sid = session['session_id']
    dest = get_destination_by_id(dest_id)
    if not dest:
        return redirect(url_for('home'))

    increment_view_count(dest_id)
    reviews = get_reviews(dest_id)
    dest = assign_badges([dest])[0]

    # Tags as list
    dest['tags_list'] = [t.strip() for t in dest['tags'].split(',')]
    dest['things_list'] = [t.strip() for t in dest['things_to_do'].split(',')]
    dest['months_list'] = [m.strip() for m in dest['best_months'].split(',')]

    # Similar places (same region, different id)
    all_dest = get_all_destinations()
    similar = [d for d in all_dest if d['region'] == dest['region'] and d['id'] != dest_id][:4]
    similar = assign_badges(similar)

    wishlist_ids = [w['id'] for w in get_wishlist(sid)]

    return render_template('detail.html',
        dest=dest,
        reviews=reviews,
        similar=similar,
        wishlist_ids=wishlist_ids
    )

# ============================================
# ROUTE 5: WISHLIST PAGE
# ============================================
@app.route('/wishlist')
def wishlist():
    ensure_session()
    sid = session['session_id']
    items = get_wishlist(sid)
    items = assign_badges(items)
    wishlist_ids = [w['id'] for w in items]
    return render_template('wishlist.html', items=items, wishlist_ids=wishlist_ids)

# ============================================
# ROUTE 6: HISTORY PAGE
# ============================================
@app.route('/history')
def history():
    ensure_session()
    sid = session['session_id']
    searches = get_search_history(sid, 20)
    return render_template('history.html', searches=searches)

# ============================================
# ROUTE 7: COMPARE PAGE
# ============================================
@app.route('/compare')
def compare():
    ensure_session()
    sid = session['session_id']
    items = get_compare_list(sid)
    return render_template('compare.html', items=items)

# ============================================
# ROUTE 8: SURPRISE ME
# ============================================
@app.route('/surprise')
def surprise():
    import random
    all_dest = get_all_destinations()
    if all_dest:
        pick = random.choice(all_dest)
        return redirect(url_for('place_detail', dest_id=pick['id']))
    return redirect(url_for('home'))

# ============================================
# API ROUTES (JSON)
# ============================================

@app.route('/api/wishlist/toggle', methods=['POST'])
def api_wishlist_toggle():
    ensure_session()
    sid = session['session_id']
    dest_id = request.json.get('dest_id')
    wishlist_ids = [w['id'] for w in get_wishlist(sid)]
    if dest_id in wishlist_ids:
        remove_from_wishlist(sid, dest_id)
        return jsonify({'status': 'removed'})
    else:
        add_to_wishlist(sid, dest_id)
        return jsonify({'status': 'added'})

@app.route('/api/compare/add', methods=['POST'])
def api_compare_add():
    ensure_session()
    sid = session['session_id']
    dest_id = request.json.get('dest_id')
    result = add_to_compare(sid, dest_id)
    if result == 'full':
        return jsonify({'status': 'full', 'msg': 'Max 3 destinations for comparison'})
    count = len(get_compare_list(sid))
    return jsonify({'status': 'added', 'count': count})

@app.route('/api/compare/clear', methods=['POST'])
def api_compare_clear():
    ensure_session()
    clear_compare(session['session_id'])
    return jsonify({'status': 'cleared'})

@app.route('/api/search/autocomplete')
def api_autocomplete():
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    results = search_by_name(q)
    return jsonify(results)

@app.route('/api/review/add', methods=['POST'])
def api_add_review():
    ensure_session()
    data = request.json
    success = add_review(
        data.get('dest_id'),
        session['session_id'],
        data.get('name', 'Anonymous'),
        data.get('rating', 5),
        data.get('comment', '')
    )
    return jsonify({'status': 'ok' if success else 'error'})

# ============================================
# RUN APP
# ============================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
