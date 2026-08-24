import os
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv

from verification.verifier import FactVerifier
from database.database import init_db, save_verification, get_history, clear_history, get_statistics

load_dotenv()

# Configure Application Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("FactVerifierApp")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key_12345')

# Initialize database tables & indexes on startup
try:
    init_db()
    logger.info("SQLite database initialized successfully.")
except Exception as err:
    logger.error(f"Failed to initialize database: {err}")

verifier = FactVerifier()


@app.route('/')
def home():
    stats = get_statistics()
    return render_template('index.html', stats=stats)


@app.route('/verify', methods=['POST'])
def verify_claim():
    claim = request.form.get('claim', '').strip()
    if not claim:
        stats = get_statistics()
        return render_template('index.html', error="Please enter a factual claim to verify.", stats=stats)

    logger.info(f"Processing verification claim: '{claim[:50]}...'")

    # Execute Fact Verification Engine safely
    try:
        res = verifier.verify(claim)
    except Exception as e:
        logger.error(f"Verification engine exception: {e}")
        res = {
            "claim": claim,
            "detected_domain": "UNKNOWN",
            "result": "UNCERTAIN ⚠️",
            "evidence_indicator": "Insufficient Evidence",
            "evidence": "Verification failed due to a system processing issue.",
            "explanation": "Live verification is temporarily unavailable. Please try again later.",
            "source": "Fact Verification Engine",
            "source_url": None,
            "verification_time": "N/A",
            "api_data": None
        }

    # Persist verification to SQLite database
    try:
        save_verification(res)
    except Exception as e:
        logger.warning(f"Database persistence warning: {e}")

    return render_template('result.html', verification=res)


@app.route('/api/verify', methods=['POST'])
def api_verify():
    """
    JSON API endpoint for client-side AJAX verification requests.
    """
    data = request.get_json(silent=True) or {}
    claim = data.get('claim', '').strip()
    if not claim:
        return jsonify({"status": "error", "message": "Please enter a valid claim."}), 400

    logger.info(f"Processing API claim: '{claim[:50]}...'")
    try:
        res = verifier.verify(claim)
    except Exception as e:
        logger.error(f"API verification engine error: {e}")
        res = {
            "claim": claim,
            "detected_domain": "UNKNOWN",
            "result": "UNCERTAIN ⚠️",
            "evidence_indicator": "Insufficient Evidence",
            "evidence": "System error during claim processing.",
            "explanation": "Live verification is temporarily unavailable. Please try again later.",
            "source": "Fact Verification Engine",
            "source_url": None,
            "verification_time": "N/A",
            "api_data": None
        }

    try:
        save_verification(res)
    except Exception as e:
        logger.warning(f"Database save failed: {e}")

    return jsonify({"status": "success", "verification": res})


@app.route('/history')
def history():
    records = get_history(limit=100)
    stats = get_statistics()
    return render_template('history.html', records=records, stats=stats)


@app.route('/history/clear', methods=['POST'])
def handle_clear_history():
    clear_history()
    logger.info("Verification history cleared by user.")
    return redirect(url_for('history'))


@app.route('/about')
def about():
    stats = get_statistics()
    return render_template('about.html', stats=stats)


@app.errorhandler(404)
def not_found_error(error):
    stats = get_statistics()
    return render_template('index.html', error="The requested page could not be found.", stats=stats), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    stats = get_statistics()
    return render_template('index.html', error="An internal server error occurred. Please try again.", stats=stats), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=port)
