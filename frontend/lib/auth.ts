/**
 * Authentication utilities
 */

import { getToken } from './api';

export const isAuthenticated = (): boolean => {
  const token = getToken();
  return !!token;
};

export const requireAuth = (): boolean => {
  return isAuthenticated();
};
