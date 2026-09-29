import axios from 'axios';

// Connects to your running FastAPI backend
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach the JWT token automatically
apiClient.interceptors.request.use(
  (config) => {
    // THE FIX: We use the exact key that the Login Page created
    const token = localStorage.getItem('riftdrop_token'); 
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle expired tokens globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token is invalid or expired. Purge the vault.
      localStorage.removeItem('riftdrop_token');
      localStorage.removeItem('riftdrop_user');
      localStorage.removeItem('riftdrop_store_id');
      
      // Force redirect to login if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;