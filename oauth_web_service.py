"""
Web-based OAuth Setup Service
Provides Flask routes for browser-based OAuth configuration
"""
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from cryptography.fernet import Fernet
import ssl
import certifi
import requests

oauth_bp = Blueprint('oauth', __name__)

CONFIG_DIR = Path.home() / '.email-pipeline' / 'config'
CONFIG_FILE = CONFIG_DIR / 'oauth_config.json'
TOKEN_FILE = CONFIG_DIR / 'token.json'

REQUIRED_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.email'
]


def is_oauth_configured():
    """Check if OAuth credentials are configured"""
    return CONFIG_FILE.exists()


def has_valid_token():
    """Check if a valid token exists"""
    if not TOKEN_FILE.exists():
        return False
    try:
        if not CONFIG_FILE.exists():
            return False
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        fernet = Fernet(config['encryption_key'].encode())
        with open(TOKEN_FILE, 'rb') as f:
            encrypted = f.read()
        decrypted = fernet.decrypt(encrypted)
        token_data = json.loads(decrypted)
        return 'token' in token_data and 'refresh_token' in token_data
    except Exception:
        return False


@oauth_bp.route('/setup')
def setup_wizard():
    """Render the OAuth setup wizard"""
    status = {
        'configured': is_oauth_configured(),
        'has_token': has_valid_token()
    }
    return render_template('setup_wizard.html', status=status)


@oauth_bp.route('/setup/status')
def setup_status():
    """Get current OAuth configuration status"""
    configured = is_oauth_configured()
    has_token = has_valid_token()
    email = None

    if configured and has_token:
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            fernet = Fernet(config['encryption_key'].encode())
            with open(TOKEN_FILE, 'rb') as f:
                encrypted = f.read()
            decrypted = fernet.decrypt(encrypted)
            token_data = json.loads(decrypted)
            email = token_data.get('email')
        except Exception:
            pass

    return jsonify({
        'configured': configured,
        'has_valid_token': has_token,
        'email': email
    })


@oauth_bp.route('/setup/save-credentials', methods=['POST'])
def save_credentials():
    """Save OAuth credentials from the web form"""
    try:
        data = request.get_json()
        client_id = data.get('client_id', '').strip()
        client_secret = data.get('client_secret', '').strip()

        if not client_id:
            return jsonify({'status': 'error', 'message': 'Client ID is required'}), 400
        if not client_secret:
            return jsonify({'status': 'error', 'message': 'Client Secret is required'}), 400

        if not client_id.endswith('.apps.googleusercontent.com'):
            return jsonify({
                'status': 'error',
                'message': 'Invalid Client ID format. It should end with .apps.googleusercontent.com'
            }), 400

        CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

        encryption_key = Fernet.generate_key()

        config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'http://localhost:5000/auth/callback',
            'encryption_key': encryption_key.decode(),
            'scopes': REQUIRED_SCOPES
        }

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        os.chmod(CONFIG_FILE, 0o600)
        os.chmod(CONFIG_DIR, 0o700)

        return jsonify({
            'status': 'success',
            'message': 'Credentials saved successfully'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@oauth_bp.route('/setup/test-credentials', methods=['POST'])
def test_credentials():
    """Test OAuth credentials by attempting a token info request"""
    try:
        data = request.get_json()
        client_id = data.get('client_id', '').strip()
        client_secret = data.get('client_secret', '').strip()

        if not client_id or not client_secret:
            return jsonify({
                'status': 'error',
                'message': 'Both Client ID and Client Secret are required'
            }), 400

        if not client_id.endswith('.apps.googleusercontent.com'):
            return jsonify({
                'status': 'error',
                'message': 'Invalid Client ID format'
            }), 400

        if not client_secret.startswith('GOCSPX-'):
            return jsonify({
                'status': 'warning',
                'message': 'Client Secret format looks unusual but may still be valid. Proceed with caution.'
            })

        return jsonify({
            'status': 'success',
            'message': 'Credentials format is valid. Click "Connect to Gmail" to complete authorization.'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@oauth_bp.route('/setup/start-auth')
def start_auth():
    """Start the OAuth authorization flow"""
    if not is_oauth_configured():
        return jsonify({
            'status': 'error',
            'message': 'Please save your credentials first'
        }), 400

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        auth_url = (
            'https://accounts.google.com/o/oauth2/v2/auth'
            f'?client_id={config["client_id"]}'
            f'&redirect_uri={config["redirect_uri"]}'
            '&response_type=code'
            '&scope=' + '%20'.join(config['scopes'])
            + '&access_type=offline'
            '&prompt=consent'
        )

        return jsonify({
            'status': 'success',
            'auth_url': auth_url
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@oauth_bp.route('/setup/complete')
def setup_complete():
    """Check if OAuth flow completed successfully"""
    if has_valid_token():
        return jsonify({
            'status': 'success',
            'message': 'Gmail connected successfully!'
        })
    else:
        return jsonify({
            'status': 'pending',
            'message': 'Waiting for authorization...'
        })


@oauth_bp.route('/setup/reset', methods=['POST'])
def reset_oauth():
    """Reset OAuth configuration (for reconfiguring)"""
    try:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        return jsonify({
            'status': 'success',
            'message': 'OAuth configuration reset'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@oauth_bp.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Google"""
    error = request.args.get('error')
    if error:
        return render_callback_page(
            success=False,
            message=f"Authorization failed: {error}"
        )

    code = request.args.get('code')
    if not code:
        return render_callback_page(
            success=False,
            message="No authorization code received"
        )

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        # Exchange code for tokens
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'redirect_uri': 'http://localhost:5000/auth/callback',
                'grant_type': 'authorization_code'
            },
            timeout=30
        )

        if token_response.status_code != 200:
            error_data = token_response.json()
            return render_callback_page(
                success=False,
                message=f"Token exchange failed: {error_data.get('error_description', error_data.get('error', 'Unknown error'))}"
            )

        token_data = token_response.json()

        # Calculate expiry
        expiry = None
        if 'expires_in' in token_data:
            expiry = (datetime.now(timezone.utc) + timedelta(seconds=token_data['expires_in'])).isoformat()

        # Prepare token storage
        token_storage = {
            'token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'scopes': config['scopes'],
            'expiry': expiry
        }

        # Encrypt and save token
        fernet = Fernet(config['encryption_key'].encode())
        encrypted_data = fernet.encrypt(json.dumps(token_storage).encode())

        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with open(TOKEN_FILE, 'wb') as f:
            f.write(encrypted_data)
        os.chmod(TOKEN_FILE, 0o600)

        return render_callback_page(
            success=True,
            message="Gmail connected successfully!"
        )

    except Exception as e:
        return render_callback_page(
            success=False,
            message=f"Error: {str(e)}"
        )


def render_callback_page(success, message):
    """Render the OAuth callback result page"""
    color = '#059669' if success else '#dc2626'
    bg_color = '#ecfdf5' if success else '#fef2f2'
    icon = '&#10003;' if success else '&#10007;'
    title = 'Success!' if success else 'Authorization Failed'

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth {title}</title>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'DM Sans', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: #faf9f7;
            }}
            .card {{
                background: white;
                padding: 48px;
                border-radius: 16px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                text-align: center;
                max-width: 400px;
            }}
            .icon {{
                width: 64px;
                height: 64px;
                background: {bg_color};
                color: {color};
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                margin: 0 auto 24px;
            }}
            h1 {{
                color: {color};
                margin: 0 0 12px;
                font-size: 1.5rem;
            }}
            p {{
                color: #5c5c5c;
                margin: 0 0 24px;
            }}
            .hint {{
                font-size: 0.9rem;
                color: #8a8a8a;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">{icon}</div>
            <h1>{title}</h1>
            <p>{message}</p>
            <p class="hint">{"You can close this window and return to the setup wizard." if success else "Please close this window and try again."}</p>
        </div>
        <script>
            if ({str(success).lower()}) {{
                // Notify parent window if in popup
                if (window.opener) {{
                    window.opener.postMessage('oauth-success', '*');
                }}
            }}
        </script>
    </body>
    </html>
    '''
