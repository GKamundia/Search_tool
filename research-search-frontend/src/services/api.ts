import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Request interceptor for API calls
api.interceptors.request.use(
  async config => {
    // For FormData, let axios set the content-type with boundary
    if (config.data instanceof FormData) {
      config.headers['Content-Type'] = undefined;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
api.interceptors.response.use(
  response => response,
  async error => {
    console.error('API error:', error);
    return Promise.reject(error);
  }
);

export default api;

