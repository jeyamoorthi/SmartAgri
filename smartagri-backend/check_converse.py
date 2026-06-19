import asyncio
import sys
import os

# Add current path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test():
    from db.mongodb import connect_db
    try:
        await connect_db()
    except Exception as db_err:
        print(f"Database connection skipped/failed: {db_err}")

    # Mock FastAPI request and current user
    from routers.voice_consultant import api_converse
    class MockRequest:
        def __init__(self):
            pass
        async def json(self):
            return {
                "audio": "",
                "text": "What is the tomato price today?",
                "lang_code": "ta",
                "is_comprehensive": False
            }
            
    req = MockRequest()
    user = {
        "_id": "603700000000000000000000",
        "id": "603700000000000000000000",
        "username": "Murugan",
        "email": "murugan@example.com",
        "present_crop": "tomato",
        "farmer_profile": {
            "state": "Tamil Nadu",
            "crop": "tomato",
            "farm_size": 2.0,
            "soil_type": "Red Soil",
            "soil_ph": 6.5
        }
    }
    
    print("Testing api_converse...")
    try:
        res = await api_converse(req, current_user=user)
        import json
        print("Response payload (UTF-8):")
        # Check if response is a JSONResponse or dict
        if hasattr(res, "body"):
            print(f"Response (JSONResponse - Status {res.status_code}):")
            print(res.body.decode('utf-8'))
        else:
            sys.stdout.buffer.write(json.dumps(res, ensure_ascii=False).encode('utf-8') + b'\n')
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
