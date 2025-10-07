/**
 * Authentication Context
 * 
 * Provides authentication state and methods throughout the application.
 * 
 * Industry Standards:
 *   - Context API for global state
 *   - Type-safe context
 *   - Persistent authentication
 *   - Automatic token refresh
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '../services/api';
import type { User, LoginCredentials, RegisterData } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider Component
 * 
 * Wraps application with authentication context.
 * 
 * @param props - Component props
 * @returns Provider component
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // TODO: Validate token and fetch user info
      setIsLoading(false);
    } else {
      setIsLoading(false);
    }
  }, []);

  /**
   * Login User
   * 
   * Authenticates user and stores token.
   * 
   * @param credentials - Login credentials
   * @throws Error if login fails
   */
  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setIsLoading(true);
      await apiClient.login(credentials);
      
      // TODO: Fetch user profile
      const mockUser: User = {
        id: '1',
        email: 'user@example.com',
        username: credentials.username,
        is_active: true,
        created_at: new Date().toISOString(),
      };
      
      setUser(mockUser);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Register New User
   * 
   * Creates new user account.
   * 
   * @param data - Registration data
   * @throws Error if registration fails
   */
  const register = async (data: RegisterData): Promise<void> => {
    try {
      setIsLoading(true);
      await apiClient.register(data);
      
      // Auto-login after registration
      await login({ username: data.username, password: data.password });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Logout User
   * 
   * Clears authentication state and token.
   */
  const logout = (): void => {
    apiClient.logout();
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * useAuth Hook
 * 
 * Custom hook for accessing authentication context.
 * 
 * @returns Authentication context
 * @throws Error if used outside AuthProvider
 * 
 * @example
 * const { user, login, logout } = useAuth();
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
