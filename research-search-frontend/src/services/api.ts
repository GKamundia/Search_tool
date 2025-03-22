import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for API calls
api.interceptors.request.use(
  async config => {
    // You can add auth tokens here if needed
    return config;
  },
  error => {
    Promise.reject(error);
  }
);

// Response interceptor for API calls
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    // Handle different error types here
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('API error:', error.response.status, error.response.data);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('API request error:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('API setup error:', error.message);
    }
    
    return Promise.reject(error);
  }
);


export default api;

