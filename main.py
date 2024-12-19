from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

app = FastAPI()

# MongoDB connection
client = AsyncIOMotorClient("mongodb+srv://cc251313:cc251313@cluster0.ods2o.mongodb.net/")
db = client.studentsDB

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI REST API!"}

@app.get("/add_message")
async def add_message(message: str, subject: Optional[str] = None, class_name: Optional[str] = None):
    doc = {"message": message, "subject": subject, "class_name": class_name}
    await db.messages.insert_one(doc)
    return {"status": "Message added successfully"}

@app.get("/messages")
async def get_messages():
    messages = await db.messages.find().to_list(100)
    return messages

@app.get("/analyze")
async def analyze(group_by: Optional[str] = None):
    pipeline = [{"$group": {"_id": f"${group_by}", "count": {"$sum": 1}}}] if group_by else []
    result = await db.messages.aggregate(pipeline).to_list(100)
    return result
