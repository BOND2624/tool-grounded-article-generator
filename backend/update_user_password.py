"""Script to update existing user password to use bcrypt."""
import sys
from app.database import SessionLocal, User
from app.auth import get_password_hash

def update_user_password():
    """Update admin user password to use bcrypt."""
    db = SessionLocal()
    try:
        # Find the admin user
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("User 'admin' not found!")
            print("Run 'python create_user.py' to create the user first.")
            return
        
        # Update password hash with bcrypt
        try:
            new_password_hash = get_password_hash("password")
            user.password_hash = new_password_hash
            db.commit()
            print("✓ Successfully updated user password to use bcrypt:")
            print("  Username: admin")
            print("  Password: password")
        except Exception as e:
            print(f"Error: Could not hash password with bcrypt: {e}")
            print("\nPlease ensure bcrypt is properly installed:")
            print("  pip uninstall bcrypt")
            print("  pip install bcrypt==4.0.1")
            sys.exit(1)
    except Exception as e:
        print(f"Error updating user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_user_password()
