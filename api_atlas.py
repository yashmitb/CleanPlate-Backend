from flask import Flask, request, jsonify
from user_preference_manager import UserFoodPreferenceManager
import json
import os
import socket
from dotenv import load_dotenv
import services

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Analysis Endpoints ---

@app.route('/api/analyze/image', methods=['POST'])
def analyze_image():
    """
    Analyze an uploaded image file for food waste.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file part"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No selected file"}), 400

        image_bytes = file.read()
        analysis_result = services.analyze_food_waste_image(image_bytes)
        return jsonify({"success": True, "analysis": analysis_result}), 200
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analyze/url', methods=['POST'])
def analyze_url():
    """
    Analyze an image from a URL for food waste.
    """
    try:
        data = request.get_json()
        if not data or 'image_url' not in data:
            return jsonify({"success": False, "error": "image_url is required"}), 400
            
        image_url = data['image_url']
        analysis_result = services.analyze_food_waste_url(image_url)
        return jsonify({"success": True, "analysis": analysis_result}), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    print("⚠️  WARNING: MONGODB_URI not set. Please set it as an environment variable or in the code.")
    print("   The app will fail when trying to connect to MongoDB.")

# Initialize the preference manager with Atlas (lazy initialization)
manager = None

def get_manager():
    """Get or initialize the preference manager."""
    global manager
    if manager is None:
        try:
            manager = UserFoodPreferenceManager(
                mongodb_uri=MONGODB_URI,
                db_name="food_preferences"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to MongoDB Atlas. "
                f"Please check your MONGODB_URI environment variable or connection string. "
                f"Error: {str(e)}"
            )
    return manager

@app.route('/api/user/preferences/update', methods=['POST'])
def update_preferences():
    """
    Update user food preferences based on waste analysis.
    
    Expected JSON body:
    {
        "user_id": "user123",
        "waste_analysis": { ... }  // Full waste analysis JSON from OpenAI
    }
    
    Returns:
    {
        "success": true,
        "user": { ... },
        "message": "Preferences updated successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        user_id = data.get('user_id')
        waste_analysis = data.get('waste_analysis')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        if not waste_analysis:
            return jsonify({
                "success": False,
                "error": "waste_analysis is required"
            }), 400
        
        # Update user preferences
        updated_user = get_manager().update_user_preferences(user_id, waste_analysis)
        
        # Remove MongoDB _id field for JSON serialization
        if '_id' in updated_user:
            del updated_user['_id']
        
        return jsonify({
            "success": True,
            "user": json.loads(json.dumps(updated_user, default=str)),
            "message": "Preferences updated successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/user/<user_id>/summary', methods=['GET'])
def get_user_summary(user_id):
    """
    Get comprehensive user summary with preferences and statistics.
    
    Returns:
    {
        "success": true,
        "summary": { ... }
    }
    """
    try:
        summary = get_manager().get_user_summary(user_id)
        
        if not summary:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        return jsonify({
            "success": True,
            "summary": summary
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/user/<user_id>/history', methods=['GET'])
def get_meal_history(user_id):
    """
    Get meal history for a user.
    
    Query params:
    - limit: Number of meals to return (default: 10)
    
    Returns:
    {
        "success": true,
        "history": [ ... ]
    }
    """
    try:
        limit = request.args.get('limit', default=10, type=int)
        
        history = get_manager().get_meal_history(user_id, limit=limit)
        
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/user/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get basic user information.
    
    Returns:
    {
        "success": true,
        "user": { ... }
    }
    """
    try:
        user = get_manager().get_user(user_id)
        
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        # Remove MongoDB _id field
        if '_id' in user:
            del user['_id']
        
        return jsonify({
            "success": True,
            "user": json.loads(json.dumps(user, default=str))
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/user/create', methods=['POST'])
def create_user():
    """
    Create a new user.
    
    Expected JSON body:
    {
        "user_id": "user123",
        "user_name": "John Doe"  // optional
    }
    
    Returns:
    {
        "success": true,
        "user": { ... },
        "message": "User created successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        # Check if user already exists
        existing_user = get_manager().get_user(user_id)
        if existing_user:
            return jsonify({
                "success": False,
                "error": "User already exists"
            }), 409
        
        # Create user
        new_user = get_manager().create_user(user_id, user_name)
        
        # Remove MongoDB _id field
        if '_id' in new_user:
            del new_user['_id']
        
        return jsonify({
            "success": True,
            "user": json.loads(json.dumps(new_user, default=str)),
            "message": "User created successfully"
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user and all their data.
    
    Returns:
    {
        "success": true,
        "message": "User deleted successfully"
    }
    """
    try:
        deleted = get_manager().delete_user(user_id)
        
        if not deleted:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "User deleted successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Food Preference API",
        "database": "MongoDB Atlas"
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

def find_free_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port."""
    for i in range(max_attempts):
        port = start_port + i
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    return None

if __name__ == '__main__':
    print("🚀 Starting Food Preference API")
    print("☁️  Using MongoDB Atlas (Cloud)")
    
    # Try to find an available port
    port = find_free_port(5000)
    if port is None:
        print("❌ Error: Could not find an available port")
        exit(1)
    
    if port != 5000:
        print(f"⚠️  Port 5000 is in use, using port {port} instead")
    
    print(f"🌐 API running on http://localhost:{port}")
    print("\n⚠️  Make sure to set your MONGODB_URI!")
    app.run(debug=True, host='0.0.0.0', port=port)