"""Database setup and models."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from app.config import settings

# Database setup
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing context - initialize lazily to avoid bcrypt issues
_pwd_context = None

def get_pwd_context():
    """Get password context, initializing if needed."""
    global _pwd_context
    if _pwd_context is None:
        _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return _pwd_context


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database and create default user if needed."""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if any users exist
        if db.query(User).first() is None:
            # Create default test user
            # Import here to avoid circular imports
            try:
                from app.auth import get_password_hash
                default_password = get_password_hash("password")
            except Exception as e:
                # If bcrypt fails, skip user creation and let user run create_user.py
                print(f"Warning: Could not hash password due to bcrypt issue: {e}")
                print("The server will start, but you'll need to create a user manually.")
                print("Run: python create_user.py")
                return
            
            default_user = User(
                username="admin",
                password_hash=default_password
            )
            db.add(default_user)
            db.commit()
            print("Created default user: admin / password")
    except Exception as e:
        print(f"Warning: Could not create default user: {e}")
        print("Run 'python create_user.py' to create a user manually.")
    finally:
        db.close()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
