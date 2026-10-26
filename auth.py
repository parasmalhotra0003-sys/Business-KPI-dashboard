from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
import bcrypt
from functools import wraps
from database.connection import execute_query, execute_update

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """
    Decorator to protect routes from unauthenticated access.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # If it's an API request, return JSON, else redirect to login page
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized access. Please login.'}), 401
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """
    Serves the login page.
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard_view'))
    return render_template('login.html')

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """
    Handles authentication via JSON/Form POST request.
    """
    data = request.get_json() or request.form
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400
        
    try:
        user = execute_query(
            "SELECT * FROM users WHERE username = %s",
            (username,),
            fetchone=True
        )
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Store in session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['role'] = user['role']
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'error': 'Invalid username or password.'}), 401
    except Exception as e:
        return jsonify({'error': f'Authentication failed: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Clears user session and redirects to login.
    """
    session.clear()
    if request.path.startswith('/api/'):
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/api/auth/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Gets or updates current user profile.
    """
    user_id = session.get('user_id')
    if request.method == 'GET':
        try:
            user = execute_query(
                "SELECT id, username, email, role, created_at FROM users WHERE id = %s",
                (user_id,),
                fetchone=True
            )
            if user:
                return jsonify({'user': user})
            return jsonify({'error': 'User not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    elif request.method == 'POST':
        data = request.get_json() or request.form
        email = data.get('email')
        new_password = data.get('password')
        
        if not email:
            return jsonify({'error': 'Email is required.'}), 400
            
        try:
            if new_password:
                hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                execute_update(
                    "UPDATE users SET email = %s, password_hash = %s WHERE id = %s",
                    (email, hashed, user_id)
                )
            else:
                execute_update(
                    "UPDATE users SET email = %s WHERE id = %s",
                    (email, user_id)
                )
            session['email'] = email
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        except Exception as e:
            return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500
