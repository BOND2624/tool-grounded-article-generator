# Tool-Grounded Article Generator

A full-stack application that generates high-quality, structured articles using AI with web search grounding. Built with FastAPI (backend) and Next.js (frontend).

## Features

- AI-powered article generation with web search grounding
- Structured JSON output (Article JSON + SEO Metadata)
- HTML rendering for articles
- JWT-based authentication
- Automatic fallback to OpenRouter when Gemini quota is exhausted
- Source URL extraction and redirect resolution

## Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the `backend` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=xiaomi/mimo-v2-flash:free
JWT_SECRET_KEY=your_secret_key_here
```

5. Get API keys:
   - Gemini API key: https://makersuite.google.com/app/apikey
   - OpenRouter API key: https://openrouter.ai/keys

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Project Locally

### Start the Backend

1. From the `backend` directory:
```bash
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### Start the Frontend

1. From the `frontend` directory:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Default Credentials

- Username: `admin`
- Password: `admin123`

## Usage

1. Open `http://localhost:3000` in your browser
2. Login with the default credentials
3. Enter your article prompt
4. Optionally provide a reference URL
5. Click "Generate Article"
6. View, regenerate, or download the generated article

## Project Structure

```
tool-grounded-article-generator/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── gemini_service.py    # AI article generation
│   ├── html_renderer.py     # HTML rendering
│   ├── auth.py              # Authentication
│   └── requirements.txt     # Python dependencies
└── frontend/
    ├── app/                 # Next.js pages
    ├── components/          # React components
    ├── lib/                 # API client & utilities
    └── package.json         # Node dependencies
```
