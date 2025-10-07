/**
 * TypeScript Type Definitions
 * 
 * Centralized type definitions for the application.
 * 
 * Industry Standards:
 *   - Strict type checking
 *   - Interface over type for extensibility
 *   - Proper null handling
 *   - Enum for constants
 */

// User Types
export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

// Prediction Types
export interface PredictionResult {
  species: string;
  species_id: number;
  confidence: number;
  inference_time_ms: number;
  model_version: string;
  timestamp: string;
  all_probabilities?: Record<string, number>;
}

export interface PredictionRequest {
  image_base64: string;
  model_version?: string;
  return_probabilities?: boolean;
}

// Task Types
export enum TaskStatus {
  PENDING = 'PENDING',
  STARTED = 'STARTED',
  SUCCESS = 'SUCCESS',
  FAILURE = 'FAILURE',
  RETRY = 'RETRY',
  REVOKED = 'REVOKED',
}

export interface TaskInfo {
  task_id: string;
  status: TaskStatus;
  result?: any;
  progress?: {
    current: number;
    total: number;
  };
  error?: string;
  created_at?: string;
  completed_at?: string;
}

// Model Types
export interface ModelInfo {
  version: string;
  architecture: string;
  num_parameters: number;
  checksum: string;
  loaded_at: string;
  performance_metrics: Record<string, number>;
  is_active: boolean;
}

// API Response Types
export interface APIError {
  error: {
    type: string;
    message: string;
    status_code: number;
    path: string;
    timestamp: string;
    details?: any;
  };
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
  checks?: Record<string, string>;
}

// Dashboard Types
export interface MetricData {
  timestamp: number;
  value: number;
}

export interface ChartData {
  name: string;
  value: number;
}

export interface DashboardStats {
  total_predictions: number;
  active_tasks: number;
  model_accuracy: number;
  avg_inference_time_ms: number;
  predictions_today: number;
  error_rate: number;
}
