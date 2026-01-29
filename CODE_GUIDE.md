# Code Guide - Article Generator System

This document provides a comprehensive guide to the codebase structure, explaining what each file does and how the system works.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Backend Structure](#backend-structure)
3. [Frontend Structure](#frontend-structure)
4. [File-by-File Breakdown](#file-by-file-breakdown)
5. [Data Flow](#data-flow)
6. [Key Components](#key-components)

---

## System Architecture

The Article Generator is a full-stack application with the following architecture:

```
┌─────────────────┐
│   Next.js UI    │  (Frontend - React/TypeScript)
└────────┬────────┘
         │ HTTP/REST API
         │ JWT Authentication
┌────────▼────────┐
│   FastAPI       │  (Backend - Python)
│   - Auth        │
│   - Articles    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│SQLite │ │Gemini │
│  DB   │ │  API  │
└───────┘ └───────┘
```

---

## Backend Structure

### Root Level Files

#### `backend/requirements.txt`
**Purpose**: Python dependency management file
- Lists all Python packages required for the backend
- Key dependencies:
  - `fastapi`: Web framework for building APIs
  - `uvicorn`: ASGI server for running FastAPI
  - `sqlalchemy`: ORM for database operations
  - `google-generativeai`: Gemini AI SDK for article generation
  - `python-jose`: JWT token handling
  - `passlib[bcrypt]`: Password hashing
  - `slowapi`: Rate limiting

#### `backend/create_user.py`
**Purpose**: Utility script to manually create users
- Creates a default admin user if none exists
- Handles bcrypt password hashing
- Useful for initial setup or password recovery

#### `backend/update_user_password.py`
**Purpose**: Utility script to update user password hashes
- Converts old SHA256 hashes to bcrypt
- Helps migrate existing users to secure password storage

### Backend Application (`backend/app/`)

#### `backend/app/__init__.py`
**Purpose**: Marks the `app` directory as a Python package
- Empty file required for Python package structure

#### `backend/app/config.py`
**Purpose**: Configuration management using environment variables
- **Key Features**:
  - Loads settings from `.env` file
  - Validates and parses CORS origins (handles comma-separated strings)
  - Defines application settings:
    - `GEMINI_API_KEY`: Google Gemini API key
    - `JWT_SECRET`: Secret for JWT token signing
    - `JWT_ALGORITHM`: Algorithm for JWT (HS256)
    - `JWT_EXPIRATION_HOURS`: Token expiration time (24 hours)
    - `DATABASE_URL`: SQLite database path
    - `CORS_ORIGINS`: Allowed frontend origins
- **Important**: Uses Pydantic settings with field validators for type conversion

#### `backend/app/database.py`
**Purpose**: Database setup and models
- **Key Components**:
  - `engine`: SQLAlchemy database engine (SQLite)
  - `SessionLocal`: Database session factory
  - `Base`: SQLAlchemy declarative base
  - `User` model: User table schema
    - `id`: Primary key
    - `username`: Unique username
    - `password_hash`: Bcrypt hashed password
    - `created_at`: Account creation timestamp
- **Functions**:
  - `get_pwd_context()`: Lazy initialization of password context (bcrypt)
  - `init_db()`: Creates tables and default admin user
  - `get_db()`: Dependency for FastAPI database sessions

#### `backend/app/auth.py`
**Purpose**: Authentication and authorization logic
- **Key Functions**:
  - `verify_password()`: Validates plain password against hash
  - `get_password_hash()`: Creates bcrypt hash from password
  - `authenticate_user()`: Validates username/password credentials
  - `create_access_token()`: Generates JWT token with expiration
  - `get_current_user()`: FastAPI dependency for protected routes
- **Security Features**:
  - Uses HTTPBearer for token extraction
  - Validates JWT signature and expiration
  - Returns 401 if authentication fails

#### `backend/app/models.py`
**Purpose**: Pydantic models for request/response validation
- **Request Models**:
  - `LoginRequest`: Username and password for login
  - `ArticleGenerateRequest`: Query and optional URL for article generation
  - `ArticleRegenerateRequest`: Existing article data and modification prompt
- **Response Models**:
  - `LoginResponse`: JWT access token
  - `ArticleGenerateResponse`: Generated article JSON, SEO metadata, and HTML
  - `ArticleRegenerateResponse`: Updated article JSON, SEO metadata, and HTML

### Backend Routers (`backend/app/routers/`)

#### `backend/app/routers/__init__.py`
**Purpose**: Marks routers directory as Python package

#### `backend/app/routers/auth.py`
**Purpose**: Authentication endpoints
- **Endpoints**:
  - `POST /api/auth/login`: User login
    - Validates credentials
    - Returns JWT token on success
    - Returns 401 on failure
- **Rate Limiting**: Integrated with slowapi (10 requests/minute)

#### `backend/app/routers/articles.py`
**Purpose**: Article generation endpoints
- **Endpoints**:
  - `POST /api/articles/generate`: Generate new article
    - Requires authentication
    - Accepts query and optional URL
    - Returns article JSON, SEO metadata, and HTML
  - `POST /api/articles/regenerate`: Modify existing article
    - Requires authentication
    - Accepts existing article and modification prompt
    - Returns updated article JSON, SEO metadata, and HTML
- **Rate Limiting**: 10 requests per minute per IP
- **Error Handling**: Comprehensive error handling with 500 status codes

### Backend Services (`backend/app/services/`)

#### `backend/app/services/__init__.py`
**Purpose**: Marks services directory as Python package

#### `backend/app/services/llm_service.py`
**Purpose**: Google Gemini AI integration for content generation
- **Key Functions**:
  - `generate_article()`: Generates article from query
    - Uses `gemini-2.5-flash` model
    - Builds structured prompt with requirements
    - Parses JSON response from LLM
    - Handles markdown formatting in content
    - Extracts sources if provided by LLM
  - `generate_seo_metadata()`: Generates SEO metadata
    - Creates optimized title, description, keywords
    - Generates Open Graph and Twitter Card metadata
  - `regenerate_article()`: Modifies existing article
    - Takes existing article and modification prompt
    - Returns updated article with same structure
- **Features**:
  - Year detection in queries (prioritizes recent info)
  - Natural handling of historical vs. recent information
  - JSON parsing with fallback for malformed responses
  - Source extraction from LLM responses

#### `backend/app/services/article_service.py`
**Purpose**: Article orchestration and HTML rendering
- **Key Functions**:
  - `markdown_to_html()`: Converts markdown to HTML
    - Handles bold text (`**text**` → `<strong>text</strong>`)
    - Converts lists (`* item` → `<ul><li>`)
    - Preserves paragraph structure
  - `create_html_document()`: Generates complete HTML document
    - Combines article content with SEO metadata
    - Renders sections with proper formatting
    - Includes links and sources sections
    - Adds inline CSS for styling
  - `generate_article_with_metadata()`: Full article generation pipeline
    - Generates article content
    - Generates SEO metadata
    - Creates HTML document
    - Returns all three components
  - `regenerate_article_with_metadata()`: Article modification pipeline
    - Regenerates article with new prompt
    - Updates SEO metadata
    - Regenerates HTML
- **HTML Features**:
  - Responsive design with mobile support
  - Styled sections, links, and sources
  - Proper semantic HTML structure
  - SEO meta tags included

#### `backend/app/main.py`
**Purpose**: FastAPI application entry point
- **Key Components**:
  - Creates FastAPI app instance
  - Initializes database on startup
  - Sets up rate limiting with slowapi
  - Configures CORS middleware
  - Includes auth and articles routers
  - Health check endpoint (`/health`)
- **Middleware**:
  - CORS: Allows frontend origins
  - Rate Limiting: Prevents abuse

---

## Frontend Structure

### Root Level Files

#### `frontend/package.json`
**Purpose**: Node.js dependency management
- Lists npm packages for frontend
- Key dependencies:
  - `next`: React framework
  - `react` & `react-dom`: UI library
  - `axios`: HTTP client for API calls
- Scripts:
  - `dev`: Development server
  - `build`: Production build
  - `start`: Production server

#### `frontend/tsconfig.json`
**Purpose**: TypeScript configuration
- Compiler options for Next.js
- Path mappings and module resolution

#### `frontend/next.config.js`
**Purpose**: Next.js configuration
- Framework settings
- Build optimizations

### Frontend Application (`frontend/app/`)

#### `frontend/app/layout.tsx`
**Purpose**: Root layout component
- Wraps all pages
- Sets HTML structure and metadata
- Includes global CSS

#### `frontend/app/globals.css`
**Purpose**: Global styles
- CSS reset and base styles
- Typography and color variables
- Responsive utilities

#### `frontend/app/page.tsx`
**Purpose**: Login page (root route)
- **Features**:
  - Username/password form
  - API authentication
  - JWT token storage in localStorage
  - Redirects to dashboard on success
  - Error handling and display
- **Styling**: Uses CSS modules (`page.module.css`)

#### `frontend/app/dashboard/page.tsx`
**Purpose**: Main article generation interface
- **Features**:
  - Protected route (requires authentication)
  - Article query form
  - Optional URL input
  - Article display area
  - SEO metadata display
  - HTML download button
  - Regenerate functionality
- **State Management**:
  - Manages article data, loading states, errors
  - Handles API calls for generation and regeneration

### Frontend Components (`frontend/components/`)

#### `frontend/components/ProtectedRoute.tsx`
**Purpose**: Route protection wrapper
- **Features**:
  - Checks for JWT token in localStorage
  - Redirects to login if not authenticated
  - Shows loading state during check
- **Usage**: Wraps protected pages

#### `frontend/components/ArticleForm.tsx`
**Purpose**: Article generation form
- **Features**:
  - Query input field
  - Optional URL input
  - Submit button with loading state
  - Error display
- **Styling**: CSS modules

#### `frontend/components/ArticleDisplay.tsx`
**Purpose**: Displays generated HTML article
- **Features**:
  - Renders HTML content in iframe
  - Download button for HTML file
  - Loading and error states
- **Styling**: CSS modules

#### `frontend/components/SEOMetadata.tsx`
**Purpose**: Displays SEO metadata
- **Features**:
  - Shows title, description, keywords
  - Displays Open Graph metadata
  - Twitter Card information
  - Collapsible sections
- **Styling**: CSS modules

### Frontend Utilities (`frontend/lib/`)

#### `frontend/lib/auth.ts`
**Purpose**: Authentication utilities
- **Functions**:
  - `getToken()`: Retrieves JWT from localStorage
  - `setToken()`: Stores JWT in localStorage
  - `removeToken()`: Removes JWT from localStorage
  - `isAuthenticated()`: Checks if user is logged in

#### `frontend/lib/api.ts`
**Purpose**: Backend API client
- **Functions**:
  - `login()`: POST to `/api/auth/login`
  - `generateArticle()`: POST to `/api/articles/generate`
  - `regenerateArticle()`: POST to `/api/articles/regenerate`
- **Features**:
  - Automatic JWT token injection
  - Error handling
  - TypeScript types for requests/responses

---

## Data Flow

### Article Generation Flow

```
1. User enters query in frontend
   ↓
2. Frontend calls POST /api/articles/generate
   ↓
3. Backend validates JWT token
   ↓
4. Backend calls generate_article_with_metadata()
   ↓
5. LLM service generates article JSON
   ↓
6. LLM service generates SEO metadata
   ↓
7. Article service creates HTML document
   ↓
8. Backend returns JSON response
   ↓
9. Frontend displays article, SEO metadata, and HTML
```

### Authentication Flow

```
1. User enters credentials
   ↓
2. Frontend calls POST /api/auth/login
   ↓
3. Backend validates credentials
   ↓
4. Backend generates JWT token
   ↓
5. Frontend stores token in localStorage
   ↓
6. Frontend includes token in subsequent requests
   ↓
7. Backend validates token on protected routes
```

---

## Key Components

### 1. Authentication System
- **JWT-based**: Stateless authentication
- **Secure**: Bcrypt password hashing
- **Protected Routes**: Frontend and backend protection

### 2. Article Generation
- **AI-Powered**: Google Gemini 2.5 Flash model
- **Structured Output**: JSON format with sections
- **SEO Optimized**: Separate metadata generation
- **HTML Rendering**: Complete styled documents

### 3. Markdown Processing
- **Bold Text**: `**text**` → `<strong>text</strong>`
- **Lists**: `* item` → `<ul><li>item</li></ul>`
- **Paragraphs**: Proper paragraph structure

### 4. Source Attribution
- **LLM Sources**: Extracts sources from AI responses
- **Display**: Dedicated sources section in HTML
- **Format**: Title, URL, and description

### 5. Rate Limiting
- **Protection**: 10 requests per minute
- **Implementation**: slowapi middleware
- **Scope**: Per IP address

---

## Environment Variables

Required `.env` file in `backend/`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=your_jwt_secret_here
DATABASE_URL=sqlite:///./article_generator.db
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login

### Articles
- `POST /api/articles/generate` - Generate new article
- `POST /api/articles/regenerate` - Regenerate existing article

### System
- `GET /` - API information
- `GET /health` - Health check

---

## Error Handling

### Backend
- **401 Unauthorized**: Invalid credentials or missing token
- **500 Internal Server Error**: LLM errors, parsing failures
- **429 Too Many Requests**: Rate limit exceeded

### Frontend
- **Network Errors**: Displayed to user
- **Validation Errors**: Form-level feedback
- **Authentication Errors**: Redirect to login

---

## Security Features

1. **Password Hashing**: Bcrypt with salt
2. **JWT Tokens**: Signed and time-limited
3. **CORS Protection**: Whitelist of allowed origins
4. **Rate Limiting**: Prevents abuse
5. **Input Validation**: Pydantic models for all inputs
6. **SQL Injection Protection**: SQLAlchemy ORM

---

## Development Workflow

1. **Backend**: Run `uvicorn app.main:app --reload` in `backend/`
2. **Frontend**: Run `npm run dev` in `frontend/`
3. **Database**: Auto-created on first run
4. **Default User**: `admin` / `password` (change in production!)

---

## Production Considerations

1. **Change Default Credentials**: Update admin password
2. **Secure JWT Secret**: Use strong random secret
3. **HTTPS**: Enable SSL/TLS
4. **Database**: Consider PostgreSQL for production
5. **Environment Variables**: Never commit `.env` files
6. **Rate Limiting**: Adjust limits based on usage
7. **CORS**: Restrict to production domain only

---

## Troubleshooting

### Common Issues

1. **Bcrypt Errors**: Reinstall `bcrypt==4.0.1`
2. **CORS Errors**: Check `CORS_ORIGINS` in `.env`
3. **JWT Errors**: Verify `JWT_SECRET` is set
4. **API Timeouts**: Google Search grounding disabled to prevent timeouts
5. **Import Errors**: Ensure virtual environment is activated

---

## Future Enhancements

1. **Google Search Grounding**: Re-enable when SDK supports it
2. **User Management**: Admin panel for user CRUD
3. **Article History**: Save generated articles
4. **Export Formats**: PDF, DOCX export
5. **Multi-language Support**: Internationalization
6. **Analytics**: Track article generation metrics

---

This guide provides a comprehensive overview of the codebase. For specific implementation details, refer to the inline comments in each file.
