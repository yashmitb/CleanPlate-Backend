import requests
import time
import sys

BASE_URL = "http://localhost:5000"

print(f"Testing server at {BASE_URL}...")

def test_health():
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return true
        else:
            print(f"❌ Health check failed: {response.status_code} {response.text}")
            return False
    except requests.ConnectionError:
        print("❌ Could not connect to server")
        return False

def test_docs():
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Docs endpoint passed")
            return True
        else:
            print(f"❌ Docs endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Docs test error: {e}")
        return False

# Simple retry logic
for i in range(5):
    if test_health():
        break
    print("Waiting for server to start...")
    time.sleep(2)

test_docs()
