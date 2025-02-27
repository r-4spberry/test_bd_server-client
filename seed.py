import asyncio
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from faker import Faker
from server import SessionLocal, User, Post, Comment  # Import models from main app

fake = Faker()

async def seed_db():
    async with SessionLocal() as session:
        users = [User(name=fake.first_name(), email=fake.email()) for _ in range(10)]
        session.add_all(users)
        await session.commit()
        
        user_ids = [user.id for user in users]
        posts = [Post(title=fake.sentence(), content=fake.paragraph(), user_id=random.choice(user_ids)) for _ in range(5)]
        session.add_all(posts)
        await session.commit()
        
        post_ids = [post.id for post in posts]
        comments = [Comment(content=fake.sentence(), post_id=random.choice(post_ids), user_id=random.choice(user_ids)) for _ in range(10)]
        session.add_all(comments)
        await session.commit()
        
        print("Database seeded successfully with random data!")

if __name__ == "__main__":
    asyncio.run(seed_db())