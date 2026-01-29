# Tool-Grounded Article Generator

A full-stack application that generates articles using AI (Google Gemini API) with web search grounding, SEO metadata generation, and HTML export capabilities.

## Features

- **AI-Powered Article Generation**: Uses Google Gemini API with Google Search grounding to generate well-researched articles
- **URL Context Support**: Optionally provide a reference URL for additional context
- **SEO Metadata Generation**: Automatically generates SEO-optimized metadata for articles
- **HTML Export**: Download generated articles as standalone HTML files
- **Article Regeneration**: Modify existing articles with custom prompts (e.g., "Make this more appealing to Gen Z")
- **Authentication**: Secure login system with JWT tokens
- **Rate Limiting**: Protection against abuse with rate limiting (10 requests/minute)
- **Modern UI**: Clean, responsive interface built with Next.js

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database management
- **SQLite**: Lightweight database for user authentication
- **JWT**: Token-based authentication
- **Google Gemini API**: AI model for article generation
- **slowapi**: Rate limiting middleware

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Axios**: HTTP client for API calls
- **CSS Modules**: Scoped styling

## Project Structure

```
article-generator/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration and environment variables
│   │   ├── database.py             # Database setup and models
│   │   ├── auth.py                 # Authentication logic and JWT
│   │   ├── models.py               # Pydantic models for requests/responses
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py      # Gemini API integration
│   │   │   └── article_service.py  # Article generation and HTML rendering
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── auth.py             # Login endpoint
│   │       └── articles.py         # Article generation endpoints
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/                        # Next.js app directory
│   │   ├── layout.tsx
│   │   ├── page.tsx                # Login page
│   │   ├── dashboard/
│   │   │   └── page.tsx            # Main article generation interface
│   │   └── globals.css
│   ├── components/
│   │   ├── ArticleDisplay.tsx      # Article HTML renderer
│   │   ├── SEOMetadata.tsx         # SEO metadata display
│   │   ├── ArticleForm.tsx         # Query and URL input form
│   │   └── ProtectedRoute.tsx     # Route protection wrapper
│   ├── lib/
│   │   ├── api.ts                  # Backend API client
│   │   └── auth.ts                 # Auth utilities and token management
│   ├── package.json
│   └── .env.local.example
├── README.md
└── .gitignore
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- npm or yarn
- Google Gemini API key ([Get one here](https://ai.google.dev/))

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the `backend` directory:
   ```bash
   cp .env.example .env
   ```

6. Edit `.env` and add your configuration:
   ```env
   GEMINI_API_KEY=your-gemini-api-key-here
   JWT_SECRET=your-secret-key-change-in-production
   DATABASE_URL=sqlite:///./article_generator.db
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

7. Run the backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env.local` file:
   ```bash
   cp .env.local.example .env.local
   ```

4. Edit `.env.local` and set the API URL:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

5. Run the development server:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

## How to Run the Project Locally

1. **Start the backend** (in one terminal):
   ```bash
   cd backend
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start the frontend** (in another terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application**:
   - Open your browser and navigate to `http://localhost:3000`
   - Login with default credentials:
     - Username: `admin`
     - Password: `password`

4. **Generate an article**:
   - Enter an article query (e.g., "Write an article about Trump and the Venezuela attack")
   - Optionally provide a reference URL
   - Click "Generate Article"
   - Wait for the article to be generated
   - View the article, SEO metadata, and download as HTML

## API Endpoints

### Authentication

- `POST /api/auth/login`
  - Request body: `{ "username": "admin", "password": "password" }`
  - Returns: `{ "access_token": "...", "token_type": "bearer" }`

### Articles

- `POST /api/articles/generate` (Protected)
  - Headers: `Authorization: Bearer <token>`
  - Request body: `{ "query": "Article topic", "url": "https://optional-url.com" }`
  - Returns: `{ "article_json": {...}, "seo_metadata_json": {...}, "html_content": "..." }`

- `POST /api/articles/regenerate` (Protected)
  - Headers: `Authorization: Bearer <token>`
  - Request body: `{ "article_json": {...}, "prompt": "Modification prompt" }`
  - Returns: `{ "article_json": {...}, "seo_metadata_json": {...}, "html_content": "..." }`

## Assumptions and Design Choices

### Assumptions

1. **Single User System**: The application is designed for single-user or small-team use. The database is initialized with a default admin user for testing.

2. **No User Registration**: As specified in requirements, only login is supported. Users must be created manually in the database or through the initialization script.

3. **Google Search Grounding**: The application uses Gemini API's built-in Google Search grounding feature. No separate search API integration is needed.

4. **Local Development**: Default configuration assumes local development with SQLite database and localhost URLs.

### Design Choices

1. **JWT Authentication**: Chosen for stateless authentication, making it easy to scale and integrate with frontend.

2. **SQLite Database**: Lightweight and sufficient for authentication needs. Can be easily migrated to PostgreSQL for production.

3. **Rate Limiting**: Implemented at 10 requests per minute per IP to prevent abuse while allowing reasonable usage.

4. **HTML Generation**: Articles are generated as complete, standalone HTML documents with embedded CSS for easy sharing and viewing.

5. **Component-Based Frontend**: Modular React components for maintainability and reusability.

6. **TypeScript**: Used in frontend for type safety and better developer experience.

7. **CSS Modules**: Scoped styling to prevent style conflicts.

8. **Error Handling**: Comprehensive error handling with user-friendly messages on both backend and frontend.

## Environment Variables

### Backend (.env)

- `GEMINI_API_KEY` (required): Your Google Gemini API key
- `JWT_SECRET` (required): Secret key for JWT token signing
- `DATABASE_URL` (optional): Database connection string (defaults to SQLite)
- `CORS_ORIGINS` (optional): Comma-separated list of allowed CORS origins

### Frontend (.env.local)

- `NEXT_PUBLIC_API_URL` (required): Backend API URL (default: http://localhost:8000)

## Default Credentials

- **Username**: `admin`
- **Password**: `password`

**Important**: Change the default password in production!

## Rate Limiting

Article generation endpoints are rate-limited to 10 requests per minute per IP address. This helps prevent abuse and manage API costs.

## Troubleshooting

### Backend Issues

1. **Database not found**: The database will be created automatically on first run. Make sure the backend has write permissions in the directory.

2. **Gemini API errors**: Verify your API key is correct and has sufficient quota.

3. **CORS errors**: Ensure `CORS_ORIGINS` in `.env` includes your frontend URL.

### Frontend Issues

1. **Cannot connect to API**: Verify `NEXT_PUBLIC_API_URL` in `.env.local` matches your backend URL.

2. **Authentication errors**: Clear localStorage and try logging in again.

3. **Build errors**: Make sure all dependencies are installed with `npm install`.

## Future Improvements

- User registration and management
- Article history and saving
- Multiple article formats (Markdown, PDF)
- Advanced SEO customization
- Article templates
- Batch article generation
- Analytics and usage tracking

## License

This project is provided as-is for demonstration purposes.

## Support

For issues or questions, please refer to the project documentation or create an issue in the repository.
