"""
Seed script to create sample accounts for each RBAC role:
1. Administrator ('admin')
2. Standard User ('user')
"""

import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.auth.passwords import hash_password

SAMPLE_ACCOUNTS = [
    {
        "role": "admin",
        "email": "admin@apisentinel.dev",
        "username": "admin",
        "password": "AdminPassword123!",
    },
    {
        "role": "user",
        "email": "developer@apisentinel.dev",
        "username": "developer",
        "password": "UserPassword123!",
    },
]

def seed():
    db = SessionLocal()
    print("================================================================")
    print("             API SENTINEL - RBAC USER SEEDING                   ")
    print("================================================================")
    
    created_accounts = []
    
    try:
        for acc in SAMPLE_ACCOUNTS:
            existing = (
                db.query(User)
                .filter((User.email == acc["email"]) | (User.username == acc["username"]))
                .first()
            )
            
            if existing:
                # Update role and password if already exists
                existing.hashed_password = hash_password(acc["password"])
                existing.role = acc["role"]
                existing.is_active = True
                print(f"[UPDATED] {acc['role'].upper()}: {acc['username']} ({acc['email']})")
            else:
                user = User(
                    email=acc["email"],
                    username=acc["username"],
                    hashed_password=hash_password(acc["password"]),
                    role=acc["role"],
                    is_active=True,
                )
                db.add(user)
                print(f"[CREATED] {acc['role'].upper()}: {acc['username']} ({acc['email']})")
            
            created_accounts.append(acc)
        
        db.commit()
        print("\nDatabase seeded successfully!")
        print("----------------------------------------------------------------")
        for acc in created_accounts:
            print(f"Role:     {acc['role'].upper()}")
            print(f"Email:    {acc['email']}")
            print(f"Username: {acc['username']}")
            print(f"Password: {acc['password']}")
            print("----------------------------------------------------------------")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to seed users: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed()
