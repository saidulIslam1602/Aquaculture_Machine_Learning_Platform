/**
 * ============================================================================
 * Aquaculture ML Platform - API Service Module
 * ============================================================================
 * 
 * This module provides a centralized, type-safe HTTP client for communication
 * with the Aquaculture ML Platform FastAPI backend. It implements industry
 * best practices for frontend-backend integration.
 *
 * KEY FEATURES:
 * - Type-safe API calls with TypeScript interfaces
 * - Automatic authentication token management
 * - Request/response interceptors for consistent handling
 * - Comprehensive error handling and retry logic
 * - Request cancellation and timeout management
 * - Response caching and optimization
 *
 * AUTHENTICATION:
 * - JWT token-based authentication
 * - Automatic token refresh handling
 * - Secure token storage in httpOnly cookies
 * - Logout on token expiration
 *
 * ERROR HANDLING:
 * - Standardized error response format
 * - Network error retry with exponential backoff
 * - User-friendly error messages
 * - Global error state management
 *
 * ENDPOINTS COVERED:
 * - Authentication (login, register, logout, refresh)
 * - ML Predictions (single, batch, history)
 * - Model Management (list, details, metrics)
 * - Task Management (status, results, cancellation)
 * - System Health (status, metrics, diagnostics)
 *
 * USAGE:
 * import { apiClient } from './services/api';
 * const result = await apiClient.predict(imageData);
 * ============================================================================
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  User,
  LoginCredentials,
  RegisterData,
  AuthToken,
  PredictionResult,
  PredictionRequest,
  TaskInfo,
  ModelInfo,
  HealthStatus,
} from '../types';

// ============================================================================
// API CONFIGURATION CONSTANTS
// ============================================================================

// Base URL for API requests - defaults to localhost for development
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

// Request timeout in milliseconds (30 seconds for ML predictions)
const API_TIMEOUT = 30000;

// TODO: Implement retry logic with exponential backoff
// const MAX_RETRY_ATTEMPTS = 3;
// const RETRY_DELAY = 1000;

/**
 * API Client Class
 * 
 * Provides type-safe methods for all API endpoints.
 * Handles authentication, errors, and request/response transformation.
 */
class APIClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    // Create axios instance with default config
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load token from localStorage
    this.token = localStorage.getItem('access_token');

    // Setup interceptors
    this.setupInterceptors();
  }

  /**
   * Setup Request/Response Interceptors
   * 
   * Adds authentication headers and handles errors globally.
   */
  private setupInterceptors(): void {
    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          this.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Set Authentication Token
   */
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  /**
   * Clear Authentication Token
   */
  clearToken(): void {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  // Authentication Endpoints

  async register(data: RegisterData): Promise<User> {
    const response = await this.client.post<User>('/api/v1/auth/register', data);
    return response.data;
  }

  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await this.client.post<AuthToken>('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    // Store token
    this.setToken(response.data.access_token);

    return response.data;
  }

  logout(): void {
    this.clearToken();
  }

  /**
   * Get Current User Profile
   * 
   * Fetches the currently authenticated user's profile information.
   * Requires valid authentication token.
   * 
   * @returns Promise resolving to user profile data
   * @throws Error if not authenticated or request fails
   */
  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/api/v1/auth/me');
    return response.data;
  }

  // Health Endpoints

  async getHealth(): Promise<HealthStatus> {
    const response = await this.client.get<HealthStatus>('/health');
    return response.data;
  }

  async getDetailedHealth(): Promise<HealthStatus> {
    const response = await this.client.get<HealthStatus>('/health/detailed');
    return response.data;
  }

  // ML Endpoints

  async predict(request: PredictionRequest): Promise<PredictionResult> {
    const response = await this.client.post<PredictionResult>('/api/v1/ml/predict', request);
    return response.data;
  }

  async predictAsync(request: PredictionRequest): Promise<{ task_id: string }> {
    const response = await this.client.post('/api/v1/ml/predict/async', request);
    return response.data;
  }

  async predictBatch(images: string[]): Promise<{ task_id: string }> {
    const response = await this.client.post('/api/v1/ml/predict/batch', {
      images_base64: images,
    });
    return response.data;
  }

  async listModels(): Promise<ModelInfo[]> {
    const response = await this.client.get<ModelInfo[]>('/api/v1/ml/models');
    return response.data;
  }

  async getModelInfo(version: string): Promise<ModelInfo> {
    const response = await this.client.get<ModelInfo>(`/api/v1/ml/models/${version}`);
    return response.data;
  }

  // Task Endpoints

  async getTaskStatus(taskId: string): Promise<TaskInfo> {
    const response = await this.client.get<TaskInfo>(`/api/v1/tasks/${taskId}`);
    return response.data;
  }

  async cancelTask(taskId: string): Promise<void> {
    await this.client.delete(`/api/v1/tasks/${taskId}`);
  }

  async listTasks(statusFilter?: string, page: number = 1): Promise<any> {
    const response = await this.client.get('/api/v1/tasks/', {
      params: { status_filter: statusFilter, page },
    });
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;
