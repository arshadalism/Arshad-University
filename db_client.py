from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
load_dotenv()

CONNECTION_STRING = os.getenv("MONGODB_URI")
client: MongoClient = AsyncIOMotorClient(CONNECTION_STRING)

print("Database Connected")
database = client.get_database("Arshad_University")

