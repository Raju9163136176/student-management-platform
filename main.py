from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from models import user
from models.user import Student, UpdateStudent, User
import bcrypt


load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
print(f"MONGO_URL: {MONGO_URL}")  # add this line
app = FastAPI()

# MONGO_URL = "mongodb+srv://mailmeraju92_db_user:Test1234@cluster0.yha1ztq.mongodb.net/"
client = AsyncIOMotorClient(MONGO_URL)
db = client["student_db"]
collection = db["students"]
users_collection  = db["users"]

@app.post("/auth/register")
async def insert_user(user: User):
    # Insert
    if await users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
   
    # Hash password:
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Store hashed password, not plain text
    await users_collection.insert_one({
        "username": user.username,
        "password": hashed_password.decode('utf-8')  # never store plain text
    })
    return {"message": "User registered successfully"}

@app.post("/students")
async def insert_student(student: Student):
    # Insert
    await collection.insert_one(student.dict())
    return {"message": "Student inserted"}


# @app.post("/students")
# async def insert_student(student: Student):
#     # Insert
#     await collection.insert_one(student.dict())
#     return {"message": "Student inserted"}

@app.get("/allstudents")
async def get_all_students():
    # Find all
    return await collection.find({}, {"_id": 0}).to_list(100)

@app.get("/students/filtered")
async def get_filtered_students():
    # Find with filter
    return await collection.find({"marks": {"$gte": 60}}, {"_id": 0}).to_list(100)

# new api here
@app.get("/students/{name}")
async def get_student_by_name(name:str):
      studentName = await collection.find({"name": name},{"_id":0}).to_list(100)
      if studentName:
          return studentName
      raise HTTPException(status_code=404, detail="Student not found, Name is incorrect or the student does not exist")

@app.put("/students/{name}")
async def update_student_marks(name: str, student: UpdateStudent):
    # name comes from URL path
    # marks comes from request body
    updateMarks = await collection.update_one(
        {"name": name}, 
        {"$set": {"marks": student.marks}}
    )
    if updateMarks.modified_count > 0:
        return {"status": "200", "message": "Student marks updated successfully"}
    # return {"status": "404", "message": "Student not found or marks already updated"}
    raise HTTPException(status_code=404, detail="Student not found or marks already updated")

@app.delete("/students/{name}")
async def delete_by_name(name:str):
    delete_stdnt = await collection.delete_one({"name":name})
    if delete_stdnt.deleted_count>0:
        return {"status": "200", "message": "Student deleted successfully"}
    # return {"status": "404", "message": "Student not found"}
    raise HTTPException(status_code=404, detail="Student not found")

