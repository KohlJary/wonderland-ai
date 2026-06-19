import axios from 'axios'

/**
 * API client for LDR Dashboard
 * 
 * Routes all requests to /api prefix (proxied by Vite to http://localhost:8000).
 * Credentials (httpOnly cookies) are automatically sent with each request.
 */
const apiClient = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default apiClient
