from pymongo import MongoClient
from datetime import datetime
from typing import Dict, List, Optional
import json

class UserFoodPreferenceManager:
    """
    Manages user food preferences in MongoDB based on food waste analysis.
    Tracks what users like and dislike, and updates preferences without duplicates.
    """
    
    def __init__(self, mongodb_uri: str = "mongodb://localhost:27017/", db_name: str = "food_preferences"):
        """
        Initialize MongoDB connection.
        
        Args:
            mongodb_uri: MongoDB connection string
            db_name: Database name
        """
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.users_collection = self.db['users']
        self.history_collection = self.db['meal_history']
        
        # Create indexes for better performance
        self.users_collection.create_index("user_id", unique=True)
        self.history_collection.create_index("user_id")
        self.history_collection.create_index("timestamp")
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """
        Get user data from database.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User document or None if not found
        """
        return self.users_collection.find_one({"user_id": user_id})
    
    def create_user(self, user_id: str, user_name: str = None) -> Dict:
        """
        Create a new user with empty preferences.
        
        Args:
            user_id: Unique user identifier
            user_name: Optional user name
            
        Returns:
            Created user document
        """
        user_doc = {
            "user_id": user_id,
            "user_name": user_name,
            "liked_foods": [],
            "disliked_foods": [],
            "meal_count": 0,
            "total_waste_percentage": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        self.users_collection.insert_one(user_doc)
        return user_doc
    
    def update_user_preferences(self, user_id: str, waste_analysis: Dict) -> Dict:
        """
        Update user food preferences based on waste analysis JSON.
        
        Args:
            user_id: Unique user identifier
            waste_analysis: JSON response from food waste analyzer API
            
        Returns:
            Updated user document
        """
        # Get or create user
        user = self.get_user(user_id)
        if not user:
            user = self.create_user(user_id)
        
        # Extract preferences from analysis
        food_prefs = waste_analysis.get('food_preferences', {})
        new_likes = food_prefs.get('likely_likes', [])
        new_dislikes = food_prefs.get('likely_dislikes', [])
        
        # Get current preferences
        current_likes = set(user.get('liked_foods', []))
        current_dislikes = set(user.get('disliked_foods', []))
        
        # Normalize food names (lowercase, strip whitespace)
        new_likes = [food.lower().strip() for food in new_likes]
        new_dislikes = [food.lower().strip() for food in new_dislikes]
        
        # Add new likes (avoiding duplicates)
        for food in new_likes:
            if food and food not in current_likes:
                # Remove from dislikes if it was there (preference changed)
                current_dislikes.discard(food)
                current_likes.add(food)
        
        # Add new dislikes (avoiding duplicates)
        for food in new_dislikes:
            if food and food not in current_dislikes:
                # Remove from likes if it was there (preference changed)
                current_likes.discard(food)
                current_dislikes.add(food)
        
        # Parse waste percentage
        waste_summary = waste_analysis.get('waste_summary', {})
        waste_percentage_str = waste_summary.get('total_waste_percentage', '0%')
        waste_percentage = float(waste_percentage_str.replace('%', ''))
        
        # Calculate running average of waste
        meal_count = user.get('meal_count', 0)
        current_avg_waste = user.get('total_waste_percentage', 0.0)
        new_avg_waste = ((current_avg_waste * meal_count) + waste_percentage) / (meal_count + 1)
        
        # Update user document
        update_result = self.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "liked_foods": sorted(list(current_likes)),
                    "disliked_foods": sorted(list(current_dislikes)),
                    "meal_count": meal_count + 1,
                    "total_waste_percentage": round(new_avg_waste, 2),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Save meal history
        self._save_meal_history(user_id, waste_analysis)
        
        # Return updated user
        return self.get_user(user_id)
    
    def _save_meal_history(self, user_id: str, waste_analysis: Dict):
        """
        Save individual meal analysis to history collection.
        
        Args:
            user_id: Unique user identifier
            waste_analysis: JSON response from food waste analyzer API
        """
        history_doc = {
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "original_meal": waste_analysis.get('original_meal', {}),
            "thrown_away": waste_analysis.get('thrown_away', []),
            "eaten": waste_analysis.get('eaten', []),
            "food_preferences": waste_analysis.get('food_preferences', {}),
            "waste_summary": waste_analysis.get('waste_summary', {})
        }
        
        self.history_collection.insert_one(history_doc)
    
    def get_user_summary(self, user_id: str) -> Optional[Dict]:
        """
        Get a comprehensive summary of user's food preferences.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User summary with preferences and statistics
        """
        user = self.get_user(user_id)
        if not user:
            return None
        
        # Get meal history count
        history_count = self.history_collection.count_documents({"user_id": user_id})
        
        # Get recent meals
        recent_meals = list(
            self.history_collection
            .find({"user_id": user_id})
            .sort("timestamp", -1)
            .limit(5)
        )
        
        # Format recent meals
        formatted_meals = []
        for meal in recent_meals:
            formatted_meals.append({
                "meal_name": meal.get('original_meal', {}).get('name', 'Unknown'),
                "timestamp": meal.get('timestamp').isoformat() if meal.get('timestamp') else None,
                "waste_percentage": meal.get('waste_summary', {}).get('total_waste_percentage', 'N/A')
            })
        
        return {
            "user_id": user.get('user_id'),
            "user_name": user.get('user_name'),
            "liked_foods": user.get('liked_foods', []),
            "disliked_foods": user.get('disliked_foods', []),
            "total_meals_analyzed": user.get('meal_count', 0),
            "average_waste_percentage": user.get('total_waste_percentage', 0.0),
            "recent_meals": formatted_meals,
            "created_at": user.get('created_at').isoformat() if user.get('created_at') else None,
            "updated_at": user.get('updated_at').isoformat() if user.get('updated_at') else None
        }
    
    def get_meal_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get meal history for a user.
        
        Args:
            user_id: Unique user identifier
            limit: Maximum number of meals to return
            
        Returns:
            List of meal history documents
        """
        meals = list(
            self.history_collection
            .find({"user_id": user_id}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
        
        # Convert datetime to string for JSON serialization
        for meal in meals:
            if 'timestamp' in meal and meal['timestamp']:
                meal['timestamp'] = meal['timestamp'].isoformat()
        
        return meals
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user and all their data.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if user was deleted, False otherwise
        """
        # Delete user document
        user_result = self.users_collection.delete_one({"user_id": user_id})
        
        # Delete all meal history
        self.history_collection.delete_many({"user_id": user_id})
        
        return user_result.deleted_count > 0
    
    def close(self):
        """Close MongoDB connection."""
        self.client.close()


# Example usage
if __name__ == "__main__":
    # Initialize the manager
    manager = UserFoodPreferenceManager()
    
    # Example waste analysis JSON (from the food waste analyzer API)
    waste_analysis = {
        "original_meal": {
            "name": "Loaded Fries",
            "description": "Fries topped with cheese and possibly other ingredients like bacon and jalapenos."
        },
        "thrown_away": [
            {
                "item": "fries",
                "quantity": "1/4 cup",
                "percentage_of_original": "30%"
            },
            {
                "item": "toppings (cheese, jalapenos)",
                "quantity": "1/8 cup",
                "percentage_of_original": "40%"
            }
        ],
        "eaten": [
            {
                "item": "fries",
                "quantity": "2/3 cup",
                "percentage_of_original": "70%"
            },
            {
                "item": "toppings",
                "quantity": "3/8 cup",
                "percentage_of_original": "60%"
            }
        ],
        "food_preferences": {
            "likely_dislikes": ["toppings"],
            "likely_likes": ["fries"],
            "insights": "The person seems to prefer plain fries over fries with toppings."
        },
        "waste_summary": {
            "total_waste_percentage": "35%",
            "waste_value": "medium"
        }
    }
    
    # Update user preferences
    user_id = "user123"
    updated_user = manager.update_user_preferences(user_id, waste_analysis)
    
    print("=== Updated User ===")
    print(json.dumps(updated_user, indent=2, default=str))
    
    # Get user summary
    summary = manager.get_user_summary(user_id)
    print("\n=== User Summary ===")
    print(json.dumps(summary, indent=2))
    
    # Get meal history
    history = manager.get_meal_history(user_id, limit=5)
    print("\n=== Meal History ===")
    print(json.dumps(history, indent=2))
    
    # Close connection
    manager.close()
