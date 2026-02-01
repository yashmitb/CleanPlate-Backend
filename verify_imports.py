import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

print("Attempting to import modules...")

try:
    import food_analysis_service
    print("✅ food_analysis_service imported successfully")
except ImportError as e:
    print(f"❌ Failed to import food_analysis_service: {e}")
    sys.exit(1)

try:
    import services
    print("✅ services imported successfully")
except ImportError as e:
    print(f"❌ Failed to import services: {e}")
    sys.exit(1)

try:
    from api_atlas import app
    print("✅ api_atlas imported successfully")
except ImportError as e:
    print(f"❌ Failed to import api_atlas: {e}")
    sys.exit(1)

print("All modules verified.")
