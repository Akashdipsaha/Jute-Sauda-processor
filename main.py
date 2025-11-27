import uvicorn
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from bson.json_util import dumps
import json

app = FastAPI(title="Jute Sauda API", description="API for SAP Integration")

# --- CONFIGURATION (Use secrets in production!) ---
# ⚠️ REPLACE WITH YOUR *NEW* PASSWORD if you changed it.
# The one in your screenshot is visible to the public internet now.
MONGO_USER = "Akashdip_Saha"
MONGO_PASSWORD = "STIL@12345" 
CLUSTER_URL = "cluster0.2zgbica.mongodb.net"

def get_mongo_collection():
    try:
        escaped_user = quote_plus(MONGO_USER)
        escaped_pass = quote_plus(MONGO_PASSWORD)
        connection_string = f"mongodb+srv://{escaped_user}:{escaped_pass}@{CLUSTER_URL}/?retryWrites=true&w=majority"
        
        client = MongoClient(connection_string, server_api=ServerApi('1'))
        db = client["ocr_project"]
        return db["sauda_data"]
    except Exception as e:
        print(f"DB Connection Error: {e}")
        return None

@app.get("/")
def home():
    return {"message": "Jute Sauda API is running. Go to /sauda to fetch data."}

@app.get("/sauda")
def get_sauda_data(limit: int = 10):
    """
    Fetches the latest 'limit' records from MongoDB.
    URL for Postman/SAP: http://localhost:8000/sauda
    """
    collection = get_mongo_collection()
    if collection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    # Fetch data, sort by latest uploaded first
    cursor = collection.find({}).sort("_id", -1).limit(limit)
    
    # Convert MongoDB BSON to standard JSON string, then back to Python dict
    # This handles ObjectID and Date formats automatically
    json_data = json.loads(dumps(cursor))
    
    return json_data

if __name__ == "__main__":
    # Runs the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)