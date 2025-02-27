# Backend: FastAPI + MySQL

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

import asyncio

DATABASE_URL = f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with SessionLocal() as session:
        yield session


# Models
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.sql import text


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


@app.on_event("startup")
async def startup():
    await init_db()


@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@app.get("/users/", response_model=List[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
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
async def get_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM posts"))
    return result.mappings().all()


@app.post("/comments/", response_model=CommentResponse)
async def create_comment(comment: CommentCreate, db: AsyncSession = Depends(get_db)):
    new_comment = Comment(
        content=comment.content, post_id=comment.post_id, user_id=comment.user_id
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


@app.get("/comments/", response_model=List[CommentResponse])
async def get_comments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM comments"))
    return result.mappings().all()


# Run with: uvicorn server:app --reload
