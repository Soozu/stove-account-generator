from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import secrets
import os
from flask_cors import CORS  # Add CORS support

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get port from Railway environment or use default
port = int(os.environ.get('PORT', 5000))

# Secret key for API authentication - use environment variable
API_KEY = os.environ.get('API_KEY', 'STOVE_ADMIN_2024_SECRET')

# Database path - use environment variable or default
DB_PATH = os.environ.get('DB_PATH', 'licenses_db.json')

@app.route('/', methods=['GET'])
def index():
    """Root endpoint for health check"""
    return jsonify({
        'status': 'online',
        'version': 'v0.2.5',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'online'}), 200

def generate_license_key():
    """Generate a unique license key"""
    timestamp = datetime.now().strftime("%Y%m")
    random_part = secrets.token_hex(6).upper()
    return f"STOVE-{timestamp}-{random_part}"

def save_license(license_data):
    """Save license data to database file"""
    try:
        licenses = {}
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r') as f:
                licenses = json.load(f)
        
        licenses[license_data['license_key']] = license_data
        
        with open(DB_PATH, 'w') as f:
            json.dump(licenses, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving license: {e}")
        return False

@app.route('/api/generate_license', methods=['POST'])
def generate_license():
    """Generate a new license key"""
    # Check API key
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        duration_days = data.get('duration_days', 30)  # Default 30 days
        discord_contact = data.get('discord_contact', '')
        
        # Generate license key
        license_key = generate_license_key()
        
        # Calculate expiry date
        created_at = datetime.now()
        expiry_date = created_at + timedelta(days=duration_days)
        
        # Create license data
        license_data = {
            'license_key': license_key,
            'user_id': user_id,
            'created_at': created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'expiry_date': expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
            'discord_contact': discord_contact,
            'is_active': True
        }
        
        # Save license
        if save_license(license_data):
            return jsonify({
                'success': True,
                'license_data': license_data
            })
        else:
            return jsonify({'error': 'Failed to save license'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate_license', methods=['GET', 'POST'])
def validate_license():
    if request.method == 'GET':
        return jsonify({'status': 'License server is running'}), 200
        
    try:
        # Get data from either JSON or raw data
        if request.is_json:
            data = request.get_json()
        else:
            try:
                data = json.loads(request.data.decode())
            except:
                return jsonify({'error': 'Invalid request format'}), 400

        if not data or 'license_key' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        license_key = data['license_key']
        
        # Load licenses database
        licenses = {}
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r') as f:
                licenses = json.load(f)
        
        # Validate license
        if license_key in licenses:
            license_data = licenses[license_key]
            try:
                # Try different date formats
                try:
                    expiry_date = datetime.strptime(license_data['expiry_date'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    expiry_date = datetime.strptime(license_data['expiry_date'], '%Y-%m-%d')
                
                if datetime.now() <= expiry_date:
                    return jsonify({
                        'valid': True,
                        'license_data': license_data
                    }), 200
            except Exception as date_error:
                print(f"Date parsing error: {date_error}")
                return jsonify({'error': 'Invalid date format in license'}), 500
                
        return jsonify({'valid': False, 'message': 'Invalid or expired license'}), 401
        
    except Exception as e:
        print(f"License validation error: {str(e)}")  # Add logging
        return jsonify({'error': str(e)}), 500

@app.route('/api/deactivate_license', methods=['POST'])
def deactivate_license():
    """Deactivate a license key"""
    # Check API key
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        
        if not license_key:
            return jsonify({'error': 'License key required'}), 400
            
        # Load licenses database
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r') as f:
                licenses = json.load(f)
        else:
            return jsonify({'error': 'License not found'}), 404
            
        # Check if license exists
        if license_key not in licenses:
            return jsonify({'error': 'Invalid license key'})
            
        # Deactivate license
        licenses[license_key]['is_active'] = False
        
        # Save changes
        with open(DB_PATH, 'w') as f:
            json.dump(licenses, f, indent=4)
            
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use Railway's PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 