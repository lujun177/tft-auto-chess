"""
Flask API and Web UI for TFT Auto Chess
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from pathlib import Path

from utils.logger import logger
from config.settings import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from main import TFTAutoChess


# Initialize Flask app
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
CORS(app)

# Initialize TFT system
tft_system = None


def init_system():
    """Initialize TFT Auto Chess system."""
    global tft_system
    try:
        tft_system = TFTAutoChess()
        logger.info("TFT system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize TFT system: {e}")


# ============ API Routes ============

@app.route('/')
def index():
    """Serve main page."""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'system': tft_system is not None
    }), 200


@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Get system information."""
    try:
        if not tft_system:
            return jsonify({'error': 'System not initialized'}), 500
        
        info = {
            'detector': tft_system.detector.get_model_info() if tft_system.detector else None,
            'recommendation_engine': 'Loaded' if tft_system.recommendation_engine else 'Not loaded',
            'winrate_data_count': len(tft_system.recommendation_engine.winrate_data)
        }
        return jsonify(info), 200
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get card recommendations."""
    try:
        if not tft_system:
            return jsonify({'error': 'System not initialized'}), 500
        
        data = request.get_json()
        current_cards = data.get('current_cards', [])
        level = data.get('level', 5)
        top_n = data.get('top_n', 5)
        
        logger.info(f"Getting recommendations for cards: {current_cards}, level: {level}")
        
        recommendations = tft_system.get_recommendations(
            current_cards=current_cards,
            level=level,
            top_n=top_n
        )
        
        result = [
            {
                'champion': champion,
                'score': float(score),
                'percentage': f'{score*100:.1f}%'
            }
            for champion, score in recommendations
        ]
        
        return jsonify({
            'success': True,
            'recommendations': result,
            'count': len(result)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/synergies', methods=['POST'])
def analyze_synergies():
    """Analyze synergies for current team."""
    try:
        if not tft_system:
            return jsonify({'error': 'System not initialized'}), 500
        
        data = request.get_json()
        current_cards = data.get('current_cards', [])
        
        logger.info(f"Analyzing synergies for: {current_cards}")
        
        analysis = tft_system.analyze_synergies(current_cards)
        
        return jsonify({
            'success': True,
            'active_synergies': analysis.get('active_synergies', {}),
            'near_completion': analysis.get('near_completion', [])
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing synergies: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/champions', methods=['GET'])
def get_champions():
    """Get list of all available champions."""
    try:
        if not tft_system or not tft_system.recommendation_engine.winrate_data:
            return jsonify({'error': 'No champion data available'}), 500
        
        champions = list(tft_system.recommendation_engine.winrate_data.keys())
        
        return jsonify({
            'success': True,
            'champions': champions,
            'count': len(champions)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting champions: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/champions/<champion>', methods=['GET'])
def get_champion_stats(champion):
    """Get stats for a specific champion."""
    try:
        if not tft_system or not tft_system.recommendation_engine.winrate_data:
            return jsonify({'error': 'No champion data available'}), 500
        
        champion_lower = champion.lower()
        if champion_lower not in tft_system.recommendation_engine.winrate_data:
            return jsonify({'error': f'Champion {champion} not found'}), 404
        
        stats = tft_system.recommendation_engine.winrate_data[champion_lower]
        
        return jsonify({
            'success': True,
            'champion': champion,
            'stats': stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting champion stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tier-list', methods=['GET'])
def get_tier_list():
    """Get champions grouped by tier."""
    try:
        if not tft_system:
            return jsonify({'error': 'System not initialized'}), 500
        
        tiers = tft_system.recommendation_engine.get_tier_recommendations()
        
        return jsonify({
            'success': True,
            'tiers': tiers
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting tier list: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh-data', methods=['POST'])
def refresh_winrate_data():
    """Refresh winrate data from source."""
    try:
        if not tft_system:
            return jsonify({'error': 'System not initialized'}), 500
        
        logger.info("Refreshing winrate data...")
        data = tft_system.winrate_fetcher.fetch_and_cache('tacticians', force_refresh=True)
        
        if data:
            tft_system.recommendation_engine.load_winrate_data(data)
            return jsonify({
                'success': True,
                'message': f'Updated data for {len(data)} champions'
            }), 200
        else:
            return jsonify({'error': 'Failed to fetch data'}), 500
    
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/demo', methods=['GET'])
def run_demo():
    """Run demo analysis."""
    try:
        if not tft_system:
            return jsonify({'error': 'System not initialized'}), 500
        
        logger.info("Running demo...")
        result = tft_system.run_demo()
        
        # Convert recommendations to serializable format
        recommendations = [
            {'champion': c, 'score': float(s), 'percentage': f'{s*100:.1f}%'}
            for c, s in result.get('recommendations', [])
        ]
        
        return jsonify({
            'success': True,
            'cards': result.get('cards', []),
            'level': result.get('level', 5),
            'recommendations': recommendations,
            'synergies': result.get('synergies', {})
        }), 200
    
    except Exception as e:
        logger.error(f"Error running demo: {e}")
        return jsonify({'error': str(e)}), 500


# ============ Error Handlers ============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ============ Main ============

def main():
    """Run Flask application."""
    logger.info("=" * 50)
    logger.info("TFT Auto Chess - Web UI")
    logger.info("=" * 50)
    
    # Initialize system
    init_system()
    
    # Run Flask app
    logger.info(f"Starting Flask server on {FLASK_HOST}:{FLASK_PORT}")
    logger.info(f"Open http://{FLASK_HOST}:{FLASK_PORT}/ in your browser")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
        use_reloader=False  # Disable reloader to avoid double initialization
    )


if __name__ == '__main__':
    main()
