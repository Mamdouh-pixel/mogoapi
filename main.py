from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from collections import Counter  # To compute the mode (most frequent)
from bson import ObjectId


app = FastAPI()

# MongoDB connection
client = AsyncIOMotorClient("mongodb+srv://cc251313:cc251313@cluster0.ods2o.mongodb.net/studentsDB?retryWrites=true&w=majority&appName=Cluster0")
db = client.studentsDB

# Function to calculate sentiment
def calculate_sentiment(message: str) -> str:
    # Simple sentiment analysis
    if "good" in message.lower():
        return "positive"
    else:
        return "negative"

# Helper function to convert MongoDB ObjectId to string
def serialize_message(message):
    message['_id'] = str(message['_id'])  # Convert ObjectId to string
    return message
    
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI REST API!"}

@app.get("/add_message")
async def add_message(message: str, subject: Optional[str] = None, class_name: Optional[str] = None):
    # Calculate sentiment for the message
    sentiment = calculate_sentiment(message)
    
    # Store message with sentiment in MongoDB
    doc = {
        "message": message,
        "subject": subject,
        "class_name": class_name,
        "sentiment": sentiment
    }
    await db.messages.insert_one(doc)
    
    return {"status": "Message added successfully", "sentiment": sentiment}

@app.get("/messages")
async def get_messages():
    messages = await db.messages.find().to_list(100)
    # Convert each message's _id to string
    serialized_messages = [serialize_message(message) for message in messages]
    return serialized_messages

@app.get("/analyze")
async def analyze(group_by: Optional[str] = None):
    # Retrieve all messages from the database
    messages = await db.messages.find().to_list(100)
    
    # Calculate sentiment for each message
    sentiment_data = [message["sentiment"] for message in messages]
    
    # Compute mode sentiment (most frequent sentiment)
    sentiment_counts = Counter(sentiment_data)
    mode_sentiment = sentiment_counts.most_common(1)[0]  # Get most common sentiment
    
    # Group sentiment analysis by subject or class_name if group_by is specified
    if group_by:
        if group_by not in ["class_name", "subject"]:
            raise HTTPException(status_code=400, detail="Invalid group_by value. Use 'class_name' or 'subject'.")
        
        # Group by the specified parameter and calculate sentiment counts for each group
        grouped_sentiments = {}
        for message in messages:
            group_value = message.get(group_by)
            sentiment = message["sentiment"]
            if group_value:
                if group_value not in grouped_sentiments:
                    grouped_sentiments[group_value] = {"positive": 0, "negative": 0}
                grouped_sentiments[group_value][sentiment] += 1
        
        return {"mode_sentiment": mode_sentiment, "grouped_sentiments": grouped_sentiments}

    # Return the mode sentiment without grouping
    return {"mode_sentiment": mode_sentiment}
