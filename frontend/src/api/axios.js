import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
  headers: { 'Content-Type': 'application/json' },
});

// JWT interceptor — attach token to every request
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('smartagri_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — redirect on 401
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('smartagri_token');
      localStorage.removeItem('smartagri_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default API;
