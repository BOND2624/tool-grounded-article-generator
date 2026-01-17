# Deployment Guide for Render

## Prerequisites

- Render account (https://render.com)
- GitHub repository with your code

## Deployment Steps

### 1. Backend Deployment (FastAPI)

1. **Create a new Web Service on Render:**
   - Go to Render Dashboard → New → Web Service
   - Connect your GitHub repository
   - Select the repository

2. **Configure Backend Service:**
   - **Name:** `tool-grounded-article-generator-backend` (or your preferred name)
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Python Version:** `3.11` or `3.12` (recommended - has better wheel support)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables:**
   - `GEMINI_API_KEY` - Your Gemini API key
   - `OPENROUTER_API_KEY` - Your OpenRouter API key
   - `OPENROUTER_MODEL` - `xiaomi/mimo-v2-flash:free` (or your preferred model)
   - `JWT_SECRET_KEY` - A random secret key for JWT tokens
   - `FRONTEND_URL` - Your frontend URL (e.g., `https://your-frontend.onrender.com`) - This will be set after frontend deployment

4. **Deploy:**
   - Click "Create Web Service"
   - Note the backend URL (e.g., `https://your-backend.onrender.com`)

### 2. Frontend Deployment (Next.js)

1. **Create a new Static Site on Render:**
   - Go to Render Dashboard → New → Static Site
   - Connect your GitHub repository
   - Select the repository

2. **Configure Frontend Service:**
   - **Name:** `tool-grounded-article-generator-frontend` (or your preferred name)
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `.next`

3. **Set Environment Variables:**
   - `NEXT_PUBLIC_API_URL` - Your backend URL from step 1 (e.g., `https://your-backend.onrender.com`)

4. **Update Frontend API Configuration:**
   - Make sure `frontend/lib/api.ts` uses `process.env.NEXT_PUBLIC_API_URL` or the environment variable

5. **Deploy:**
   - Click "Create Static Site"
   - Note the frontend URL

### 3. Update Backend Environment Variable

1. **After Frontend Deployment:**
   - Go back to your Backend service settings on Render
   - Add/Update the `FRONTEND_URL` environment variable with your frontend URL
   - The CORS is already configured to read from this environment variable
   - Redeploy the backend if needed

### 4. Verify Deployment

1. Visit your frontend URL
2. Test login with default credentials (`admin` / `admin123`)
3. Generate a test article
4. Verify backend API is accessible

## Important Notes

- **Python Version:** The `backend/runtime.txt` file specifies Python 3.11.9 for better compatibility with pre-built wheels
- **Backend Auto-Deploy:** Render will auto-deploy on every push to your main branch
- **Free Tier Limits:** Render free tier services spin down after 15 minutes of inactivity
- **Environment Variables:** Keep API keys secure - never commit them to Git
- **Build Time:** First deployment may take 5-10 minutes
- **Cold Starts:** Free tier services may have cold start delays (~30 seconds)
- **Wheel Support:** Using Python 3.11 ensures all packages have pre-built wheels, avoiding Rust compilation issues

## Alternative: Deploy Both as Web Services

If you prefer, you can deploy the frontend as a Web Service instead of Static Site:

1. **Frontend as Web Service:**
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Start Command:** `cd frontend && npm start`
   - **Environment:** `Node`

This approach is better if you need server-side features, but Static Site is simpler for this app.
