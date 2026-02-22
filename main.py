from fastapi import FastAPI
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
app = FastAPI()

# MONGO_URL = "mongodb+srv://mailmeraju92_db_user:Test1234@cluster0.yha1ztq.mongodb.net/"
client = AsyncIOMotorClient(MONGO_URL)
db = client["student_db"]
collection = db["students"]

class Student(BaseModel):
    name: str
    marks: float

@app.post("/students")
async def insert_student(student: Student):
    # Insert
    await collection.insert_one(student.dict())
    return {"message": "Student inserted"}

@app.get("/allstudents")
async def get_all_students():
    # Find all
    return await collection.find({}, {"_id": 0}).to_list(100)

@app.get("/students/filtered")
async def get_filtered_students():
    # Find with filter
    return await collection.find({"marks": {"$gte": 60}}, {"_id": 0}).to_list(100)

# new api here
