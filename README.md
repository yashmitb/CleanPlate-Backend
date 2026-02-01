# Food Preference Management API

A complete system for tracking user food preferences based on food waste analysis using OpenAI Vision API and MongoDB.

## Features

- 📸 Analyze food waste from images using OpenAI GPT-4o Vision
- 👤 Track individual user food preferences (likes/dislikes)
- 📊 Store meal history and waste statistics
- 🔄 Automatically update preferences without duplicates
- 🚀 RESTful API for easy integration

## Architecture

1. **food_waste_analyzer_v2.py** - Analyzes food images using OpenAI Vision API
2. **user_preference_manager.py** - MongoDB-based preference management
3. **api.py** - Flask REST API for client integration

## Installation

### Prerequisites
- Python 3.8+
- MongoDB (local or cloud)
- OpenAI API key

### Setup

```bash
# Install dependencies
pip install -r requirements_full.txt

# Start MongoDB (if running locally)
mongod

# Set your OpenAI API key in food_waste_analyzer_v2.py
# Line 7: openai.api_key = "your-api-key-here"

# Run the API server
python api.py
```

The API will start on `http://localhost:5000`

## API Endpoints

### 1. Update User Preferences
Analyze a meal and update user preferences.

**Endpoint:** `POST /api/user/preferences/update`

**Request Body:**
```json
{
  "user_id": "user123",
  "waste_analysis": {
    "original_meal": {
      "name": "Loaded Fries",
      "description": "Fries topped with cheese and jalapenos"
    },
    "thrown_away": [
      {
        "item": "fries",
        "quantity": "1/4 cup",
        "percentage_of_original": "30%"
      }
    ],
    "eaten": [
      {
        "item": "fries",
        "quantity": "2/3 cup",
        "percentage_of_original": "70%"
      }
    ],
    "food_preferences": {
      "likely_dislikes": ["toppings"],
      "likely_likes": ["fries"],
      "insights": "Person prefers plain fries"
    },
    "waste_summary": {
      "total_waste_percentage": "35%",
      "waste_value": "medium"
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "user_id": "user123",
    "liked_foods": ["fries", "chicken", "rice"],
    "disliked_foods": ["toppings", "broccoli"],
    "meal_count": 5,
    "total_waste_percentage": 28.5,
    "updated_at": "2026-01-31T10:30:00"
  },
  "message": "Preferences updated successfully"
}
```

### 2. Get User Summary
Get comprehensive user information.

**Endpoint:** `GET /api/user/<user_id>/summary`

**Response:**
```json
{
  "success": true,
  "summary": {
    "user_id": "user123",
    "user_name": null,
    "liked_foods": ["fries", "chicken", "rice"],
    "disliked_foods": ["toppings", "broccoli"],
    "total_meals_analyzed": 5,
    "average_waste_percentage": 28.5,
    "recent_meals": [
      {
        "meal_name": "Loaded Fries",
        "timestamp": "2026-01-31T10:30:00",
        "waste_percentage": "35%"
      }
    ]
  }
}
```

### 3. Get Meal History
Retrieve user's meal history.

**Endpoint:** `GET /api/user/<user_id>/history?limit=10`

**Response:**
```json
{
  "success": true,
  "history": [
    {
      "user_id": "user123",
      "timestamp": "2026-01-31T10:30:00",
      "original_meal": {
        "name": "Loaded Fries",
        "description": "..."
      },
      "thrown_away": [...],
      "eaten": [...]
    }
  ],
  "count": 1
}
```

### 4. Create User
Create a new user.

**Endpoint:** `POST /api/user/create`

**Request Body:**
```json
{
  "user_id": "user123",
  "user_name": "John Doe"
}
```

### 5. Get User
Get basic user info.

**Endpoint:** `GET /api/user/<user_id>`

### 6. Delete User
Delete user and all their data.

**Endpoint:** `DELETE /api/user/<user_id>`

### 7. Health Check
Check API status.

**Endpoint:** `GET /api/health`

## Complete Workflow Example

### Step 1: Analyze Food Image
```python
from food_waste_analyzer_v2 import analyze_food_waste
import requests

# Analyze image
result = analyze_food_waste("leftover_meal.jpg")
print(result)
```

### Step 2: Update User Preferences via API
```python
import requests

# Send to API
response = requests.post(
    'http://localhost:5000/api/user/preferences/update',
    json={
        'user_id': 'user123',
        'waste_analysis': result
    }
)

print(response.json())
```

### Step 3: Get User Summary
```python
response = requests.get('http://localhost:5000/api/user/user123/summary')
print(response.json())
```

## MongoDB Schema

### Users Collection
```javascript
{
  user_id: "user123",           // Unique identifier
  user_name: "John Doe",        // Optional
  liked_foods: ["fries", ...],  // Array of liked foods
  disliked_foods: ["broccoli", ...], // Array of disliked foods
  meal_count: 5,                // Total meals analyzed
  total_waste_percentage: 28.5, // Average waste across all meals
  created_at: ISODate("..."),
  updated_at: ISODate("...")
}
```

### Meal History Collection
```javascript
{
  user_id: "user123",
  timestamp: ISODate("..."),
  original_meal: {...},
  thrown_away: [...],
  eaten: [...],
  food_preferences: {...},
  waste_summary: {...}
}
```

## Key Features

### ✅ Duplicate Prevention
- Foods are normalized (lowercase, trimmed)
- Set-based logic prevents duplicates
- If a food moves from dislike to like, it's automatically removed from dislikes

### 📊 Running Statistics
- Average waste percentage calculated across all meals
- Meal count tracking
- Historical data preservation

### 🔄 Preference Evolution
- Preferences update based on new data
- If someone starts liking something they disliked, it updates automatically
- All changes are tracked in meal history

## Testing with cURL

```bash
# Create user
curl -X POST http://localhost:5000/api/user/create \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "user_name": "Test User"}'

# Update preferences
curl -X POST http://localhost:5000/api/user/preferences/update \
  -H "Content-Type: application/json" \
  -d @example_request.json

# Get summary
curl http://localhost:5000/api/user/test_user/summary

# Get history
curl http://localhost:5000/api/user/test_user/history?limit=5
```

## Environment Variables (Optional)

```bash
export MONGODB_URI="mongodb://localhost:27017/"
export DB_NAME="food_preferences"
export OPENAI_API_KEY="your-api-key"
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message here"
}
```

HTTP Status Codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 404: Not Found
- 409: Conflict (user already exists)
- 500: Internal Server Error

## License

MIT
