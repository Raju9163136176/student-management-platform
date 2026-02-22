from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field, validator
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
    name: str = Field(..., min_length=2, max_length=50)
    marks: float = Field(..., ge=0, le=100)
class UpdateStudent(BaseModel):
    marks: float = Field(..., ge=0, le=100)

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

