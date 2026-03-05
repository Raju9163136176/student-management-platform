from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from models.user import Student, UpdateStudent, User
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request


load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

print(f"MONGO_URL: {MONGO_URL}")  # add this line
app = FastAPI()

# MONGO_URL = "mongodb+srv://mailmeraju92_db_user:Test1234@cluster0.yha1ztq.mongodb.net/"
client = AsyncIOMotorClient(MONGO_URL)
db = client["student_db"]
collection = db["students"]
users_collection  = db["users"]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

#rate limiting code
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create token
def create_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=30)
    payload = {
        "sub": username,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")



@app.get("/protected")
async def protected_route(username: str = Depends(verify_token)):
    return {"message": f"Hello {username}, you are authenticated"}

@app.post("/auth/login")
@limiter.limit("3/minute")
async def login(request: Request, user: User):
    db_user = await users_collection.find_one({"username":user.username})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid user name")
    if bcrypt.checkpw(user.password.encode("utf-8"),db_user['password'].encode('utf-8')):
        token =create_token(user.username)
        return {"access_token":token, "token_type":"bearer","message": "User logged in successfully"}
    else: raise HTTPException(status_code=401, detail="Invalid password or username")


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
async def insert_student(student: Student, username: str = Depends(verify_token)):
    # Insert
    await collection.insert_one(student.model_dump())
    return {"message": f"Student inserted by {username}"}

@app.get("/allstudents")
async def get_all_students(username: str = Depends(verify_token)):
    # Find all
    return await collection.find({}, {"_id": 0}).to_list(100)

@app.get("/students/filtered")
async def get_filtered_students(username: str = Depends(verify_token)):
    # Find with filter
    return await collection.find({"marks": {"$gte": 60}}, {"_id": 0}).to_list(100)

# new api here
@app.get("/students/{name}")
async def get_student_by_name(name:str,username: str = Depends(verify_token)):
      studentName = await collection.find({"name": name},{"_id":0}).to_list(100)
      if studentName:
          return studentName
      raise HTTPException(status_code=404, detail="Student not found, Name is incorrect or the student does not exist")

@app.put("/students/{name}")
async def update_student_marks(name: str, student: UpdateStudent,username: str = Depends(verify_token)):
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
async def delete_by_name(name:str,username: str = Depends(verify_token)):
    delete_stdnt = await collection.delete_one({"name":name})
    if delete_stdnt.deleted_count>0:
        return {"status": "200", "message": "Student deleted successfully"}
    # return {"status": "404", "message": "Student not found"}
    raise HTTPException(status_code=404, detail="Student not found")


