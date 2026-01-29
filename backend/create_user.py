"""Script to create a default user manually."""
import sys
from app.database import SessionLocal, User, Base, engine
from app.auth import get_password_hash

def create_default_user():
    """Create default admin user."""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("User 'admin' already exists!")
            return
        
        # Create default user
        try:
            password_hash = get_password_hash("password")
            print("Using bcrypt for password hashing (secure).")
        except Exception as e:
            print(f"Error: Could not hash password with bcrypt: {e}")
            print("\nPlease fix bcrypt installation:")
            print("  pip uninstall bcrypt")
            print("  pip install bcrypt==4.0.1")
            print("\nOr upgrade:")
            print("  pip install --upgrade bcrypt")
            print("\nThen run this script again.")
            sys.exit(1)
        
        default_user = User(
            username="admin",
            password_hash=password_hash
        )
        db.add(default_user)
        db.commit()
        print("✓ Successfully created default user:")
        print("  Username: admin")
        print("  Password: password")
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_default_user()
