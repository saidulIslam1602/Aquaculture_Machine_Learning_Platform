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

  // Initialize authentication state on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Check if user has valid session
        const currentUser = await apiClient.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        // No valid session, user needs to login
        console.log('No valid authentication session');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  /**
   * Login User
   * 
   * Authenticates user with backend API and establishes session.
   * Uses httpOnly cookies for secure token storage.
   * 
   * @param credentials - User login credentials
   * @throws Error if authentication fails
   */
  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setIsLoading(true);
      
      // Authenticate with backend API
      await apiClient.login(credentials);
      
      // Fetch complete user profile
      const userProfile = await apiClient.getCurrentUser();
      
      setUser(userProfile);
    } catch (error) {
      // Re-throw error for component-level handling
      throw error;
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
