/** Backend API client. */
import axios from 'axios';
import { getAuthToken, removeAuthToken } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeAuthToken();
      if (typeof window !== 'undefined') {
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface ArticleGenerateRequest {
  query: string;
  url?: string;
}

export interface ArticleGenerateResponse {
  article_json: any;
  seo_metadata_json: any;
  html_content: string;
}

export interface ArticleRegenerateRequest {
  article_json: any;
  prompt: string;
}

export interface ArticleRegenerateResponse {
  article_json: any;
  seo_metadata_json: any;
  html_content: string;
}

export const api = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/api/auth/login', credentials);
    return response.data;
  },

  generateArticle: async (data: ArticleGenerateRequest): Promise<ArticleGenerateResponse> => {
    const response = await apiClient.post<ArticleGenerateResponse>('/api/articles/generate', data);
    return response.data;
  },

  regenerateArticle: async (data: ArticleRegenerateRequest): Promise<ArticleRegenerateResponse> => {
    const response = await apiClient.post<ArticleRegenerateResponse>('/api/articles/regenerate', data);
    return response.data;
  },
};

export default apiClient;
