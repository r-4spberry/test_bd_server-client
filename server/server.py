from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.sql import text
import asyncio

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL_MASTER = f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_MASTER_HOST')}/{os.getenv('DB_NAME')}"
DATABASE_URL_REPLICA = f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_REPLICA_HOST')}/{os.getenv('DB_NAME')}"

master_engine = create_async_engine(DATABASE_URL_MASTER, echo=True)
replica_engine = create_async_engine(DATABASE_URL_REPLICA, echo=True)

SessionLocal = sessionmaker(bind=master_engine, class_=AsyncSession, expire_on_commit=False)
ReadSessionLocal = sessionmaker(bind=replica_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Initialize database
async def init_db():
    async with master_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency for database sessions
async def get_db():
    async with SessionLocal() as session:
        yield session

async def get_read_db():
    async with ReadSessionLocal() as session:
        yield session

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    posts = relationship("Post", back_populates="owner")
    comments = relationship("Comment", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")

# Pydantic Models
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(UserCreate):
    id: int
    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    title: str
    content: str
    user_id: int

class PostResponse(PostCreate):
    id: int
    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str
    post_id: int
    user_id: int

class CommentResponse(CommentCreate):
    id: int
    class Config:
        from_attributes = True

# FastAPI App
app = FastAPI()

async def wait_for_db():
    """Retry connecting to MySQL until it's ready."""
    retries = 10
    while retries > 0:
        try:
            async with master_engine.begin() as conn:
                await conn.run_sync(lambda x: None)
            async with replica_engine.begin() as conn:
                await conn.run_sync(lambda x: None)
            print("✅ Database is ready!")
            return
        except Exception as e:
            print(f"⚠️ Waiting for database... {retries} attempts left. Error: {e}")
            retries -= 1
            await asyncio.sleep(5)
    print("❌ Database failed to start.")
    exit(1)

@app.on_event("startup")
async def startup():
    await wait_for_db()
    await init_db()

# CRUD Endpoints
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.get("/users/", response_model=List[UserResponse])
async def get_users(db: AsyncSession = Depends(get_read_db)):
    result = await db.execute(text("SELECT * FROM users"))
    return result.mappings().all()

@app.post("/posts/", response_model=PostResponse)
async def create_post(post: PostCreate, db: AsyncSession = Depends(get_db)):
    new_post = Post(title=post.title, content=post.content, user_id=post.user_id)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post

@app.get("/posts/", response_model=List[PostResponse])
async def get_posts(db: AsyncSession = Depends(get_read_db)):
    result = await db.execute(text("SELECT * FROM posts"))
    return result.mappings().all()

@app.post("/comments/", response_model=CommentResponse)
async def create_comment(comment: CommentCreate, db: AsyncSession = Depends(get_db)):
    new_comment = Comment(content=comment.content, post_id=comment.post_id, user_id=comment.user_id)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment

@app.get("/comments/", response_model=List[CommentResponse])
async def get_comments(db: AsyncSession = Depends(get_read_db)):
    result = await db.execute(text("SELECT * FROM comments"))
    return result.mappings().all()

# Run with: uvicorn server:app --reload