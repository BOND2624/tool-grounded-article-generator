/**
 * API client for backend communication
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface GenerateRequest {
  prompt: string;
  reference_url?: string;
}

export interface GenerateResponse {
  article_json: {
    title: string;
    sections: Array<{
      heading: string;
      content: string;
      sources: string[];
    }>;
    summary: string;
  };
  seo_json: {
    meta_title: string;
    meta_description: string;
    keywords: string[];
    canonical_url: string;
  };
  rendered_html: string;
  sources: string[];
}

export interface RegenerateRequest {
  existing_article_json: any;
  refinement_prompt: string;
}

// Token management
export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
};

export const setToken = (token: string): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem('auth_token', token);
};

export const removeToken = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('auth_token');
};

// API functions
export const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
};

export const generateArticle = async (request: GenerateRequest): Promise<GenerateResponse> => {
  const token = getToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_URL}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Generation failed');
  }

  return response.json();
};

export const regenerateArticle = async (request: RegenerateRequest): Promise<GenerateResponse> => {
  const token = getToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_URL}/regenerate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Regeneration failed');
  }

  return response.json();
};
