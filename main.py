from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from collections import Counter  # To compute the mode (most frequent)
from bson import ObjectId
from textblob import TextBlob  # Import TextBlob for sentiment analysis

app = FastAPI()

# MongoDB connection
client = AsyncIOMotorClient("mongodb+srv://cc251313:cc251313@cluster0.ods2o.mongodb.net/studentsDB?retryWrites=true&w=majority&appName=Cluster0")
db = client.studentsDB

# Function to calculate sentiment using TextBlob
def calculate_sentiment(message: str) -> str:
    # Perform sentiment analysis using TextBlob
    blob = TextBlob(message)
    sentiment_score = blob.sentiment.polarity  # Get polarity score
    
    # Determine sentiment based on polarity score
    if sentiment_score > 0:
        return "positive"
    elif sentiment_score < 0:
        return "negative"
    else:
        return "neutral"  # Optional: You can handle neutral cases too.

# Helper function to convert MongoDB ObjectId to string
def serialize_message(message):
    message['_id'] = str(message['_id'])  # Convert ObjectId to string
    return message

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI REST API!"}

@app.get("/add_message")
async def add_message(message: str, name:str , age:int , subject: Optional[str] = None, class_name: Optional[str] = None):
    # Calculate sentiment for the message using TextBlob
    sentiment = calculate_sentiment(message)
    
    # Store message with sentiment in MongoDB
    doc = {
        "message": message,
        "name" : name,
        "age": age,
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
    
    # Filter out messages without a "sentiment" field
    sentiment_data = [message["sentiment"] for message in messages if "sentiment" in message]
    
    if not sentiment_data:
        raise HTTPException(status_code=404, detail="No messages with sentiment data found.")
    
    # Count all sentiment occurrences
    sentiment_counts = Counter(sentiment_data)
    mode_sentiment = sentiment_counts.most_common(1)[0]  # Get the most frequent sentiment

    # Prepare response data
    response = {
        "mode_sentiment": mode_sentiment,  # Most frequent sentiment and its count
        "sentiment_counts": {
            "positive": sentiment_counts.get("positive", 0),  # Get count of positive sentiments
            "negative": sentiment_counts.get("negative", 0),  # Get count of negative sentiments
        }
    }

    # Group sentiment analysis by subject or class_name if group_by is specified
    if group_by:
        if group_by not in ["class_name", "subject"]:
            raise HTTPException(status_code=400, detail="Invalid group_by value. Use 'class_name' or 'subject'.")
        
        # Group by the specified parameter and calculate sentiment counts for each group
        grouped_sentiments = {}
        for message in messages:
            group_value = message.get(group_by)
            sentiment = message.get("sentiment")
            if group_value and sentiment:
                if group_value not in grouped_sentiments:
                    grouped_sentiments[group_value] = {"positive": 0, "negative": 0}
                grouped_sentiments[group_value][sentiment] += 1
        
        response["grouped_sentiments"] = grouped_sentiments

    return response

@app.get("/clear")
async def clear_messages():
    # Delete all documents from the "messages" collection
    result = await db.messages.delete_many({})
    
    # Return the count of deleted documents
    return {"status": "All messages deleted successfully", "deleted_count": result.deleted_count}
