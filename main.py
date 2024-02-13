from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from pydantic import BaseModel, constr, conlist
from typing import List

app = FastAPI()


# MongoDB Connection
DATABASE_URI = "mongodb+srv://vlncyAdmin:pkXLZbf8aEMl75FA@cluster0.rnvv0bk.mongodb.net/"
DB_NAME = "vlncy"
COLLECTION_NAME = "users"


# FastAPI Dependency for MongoDB connection
def get_db():
    client = MongoClient(DATABASE_URI)
    db = client[DB_NAME]
    try:
        yield db
    finally:
        client.close()

# Pydantic models
class Preferences(BaseModel):
    distance: conlist(float, min_length=2, max_length=2) # type: ignore
    age: conlist(int, min_length=2, max_length=2) # type: ignore

class Match(BaseModel):
    user_id: constr(strip_whitespace=True, max_length=10) # type: ignore
    similarity_score: float

class UserData(BaseModel):
    user_id: constr(strip_whitespace=True, max_length=10) # type: ignore
    user_zip: constr(strip_whitespace=True) # type: ignore
    user_age: int
    gender: constr(strip_whitespace=True) # type: ignore
    pref_distance: conlist(float, min_length=2, max_length=2) # type: ignore
    pref_age: conlist(int, min_length=2, max_length=2) # type: ignore
    user_matches: dict[str, float] = {}

# Event handler for startup
@app.on_event("startup")
def startup_event():
    print("FastAPI server has started successfully!")
    
    
# PATCH API to update user data
@app.patch("/userdata/{user_id}")
def update_user_data(user_id: str, updated_data: UserData, db: MongoClient = Depends(get_db)):
    user = db[COLLECTION_NAME].find_one({"user_id": user_id})
    if user:
        # Update only the fields that are provided in updated_data
        update_query = {"$set": updated_data.dict(exclude_unset=True)}
        db[COLLECTION_NAME].update_one({"user_id": user_id}, update_query)
        return {"message": "User data updated successfully"}
    raise HTTPException(status_code=404, detail="User not found")

# DELETE API to remove user data by user_id
@app.delete("/userdata/{user_id}")
def delete_user_data(user_id: str, db: MongoClient = Depends(get_db)):
    user = db[COLLECTION_NAME].find_one({"user_id": user_id})
    if user:
        db[COLLECTION_NAME].delete_one({"user_id": user_id})
        return {"message": "User data deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")

# POST API to add user data
@app.post("/userdata/")  
def create_user_data(user_data: UserData, db: MongoClient = Depends(get_db)):
    user_dict = user_data.dict()
    result = db[COLLECTION_NAME].insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    return user_dict

# GET API to retrieve user data by user_id
@app.get("/userdata/{user_id}", response_model=UserData)
def read_user_data(user_id: str, db: MongoClient = Depends(get_db)):
    user = db[COLLECTION_NAME].find_one({"user_id": user_id})
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")

# GET API to retrieve user matches by user_id
@app.get("/usermatches/{user_id}", response_model=list[Match])
def read_user_matches(user_id: str, db: MongoClient = Depends(get_db)):
    user = db[COLLECTION_NAME].find_one({"user_id": user_id})
    if user:
        matches = [{"user_id": match_user_id, "similarity_score": score} for match_user_id, score in user.get("user_matches", {}).items()]
        return matches
    raise HTTPException(status_code=404, detail="User not found")

# GET API to retrieve all user data
@app.get("/userdata/", response_model=List[UserData])
def read_all_user_data(db: MongoClient = Depends(get_db)):
    users = db[COLLECTION_NAME].find()
    return [user for user in users]
