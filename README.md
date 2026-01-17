# Tool-Grounded Article Generator

A lightweight full-stack application that allows authenticated users to generate high-quality, structured articles using AI with web search grounding and optional URL context.

## Tech Stack

- **Backend**: FastAPI, Python, JWT Auth, Ollama (local LLM)
- **Frontend**: Next.js, React, Tailwind CSS

## Project Structure

```
.
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
└── README.md
```

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Development

### Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
```

## Environment Variables

### Backend

Create `backend/.env`:
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
JWT_SECRET_KEY=your_secret_key_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

**Note**: 
- Make sure Ollama is installed and running locally: https://ollama.ai
- Pull a model: `ollama pull llama3.2` (or llama3, mistral, etc.)
- Default model is `llama3.2` but can be changed in `.env`

### Frontend

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

**Note**: These are hardcoded for development. In production, implement proper user management.

## Features

✅ JWT-based authentication  
✅ Article generation with AI (Ollama local models)  
✅ Optional reference URL context  
✅ SEO metadata generation  
✅ HTML rendering and download  
✅ Article regeneration with refinement prompts  
✅ Protected routes (frontend and backend)  
✅ Modern UI with Tailwind CSS  

## API Endpoints

- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info (protected)
- `POST /generate` - Generate article (protected)
- `POST /regenerate` - Regenerate article with refinements (protected)

## Testing

1. Start the backend:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:3000 in your browser
4. Login with default credentials
5. Generate your first article!
