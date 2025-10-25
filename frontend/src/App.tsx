/**
 * ============================================================================
 * Aquaculture ML Platform - Main React Application Component
 * ============================================================================
 * 
 * This is the root component of the Aquaculture ML Platform frontend application.
 * It orchestrates the entire React application architecture including:
 *
 * CORE FEATURES:
 * - Client-side routing with React Router
 * - Global state management via React Query and Zustand
 * - Material-UI theming and component library
 * - Authentication context and protected routes
 * - Global error handling and notifications
 * - Progressive Web App (PWA) capabilities
 *
 * ARCHITECTURE:
 * - Provider pattern for dependency injection
 * - Component-based architecture with TypeScript
 * - Centralized API state management with React Query
 * - Theme customization for consistent UI/UX
 * - Protected route wrapper for authentication
 *
 * INTEGRATIONS:
 * - FastAPI backend communication via Axios
 * - Real-time notifications with react-hot-toast
 * - Data visualization with Recharts
 * - File uploads with react-dropzone
 * - Date handling with date-fns
 *
 * DEVELOPMENT:
 * - Hot module replacement for fast development
 * - TypeScript for type safety and better DX
 * - ESLint for code quality and consistency
 * - Vite for fast build and development server
 * ============================================================================
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme, CssBaseline, Box, Typography } from '@mui/material';
import { Toaster } from 'react-hot-toast';

// Application-specific components and contexts
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Dashboard from './pages/Dashboard';

// ============================================================================
// REACT QUERY CONFIGURATION
// ============================================================================
// Global configuration for server state management and caching

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,  // Don't refetch when window regains focus
      retry: 1,                     // Retry failed requests once
      staleTime: 30000,            // Consider data fresh for 30 seconds
      gcTime: 5 * 60 * 1000,       // Keep unused data in cache for 5 minutes
    },
    mutations: {
      retry: 0,                     // Don't retry mutations automatically
    },
  },
});

// ============================================================================
// MATERIAL-UI THEME CONFIGURATION
// ============================================================================
// Custom theme for consistent design system across the application

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',            // Ocean blue - represents aquaculture
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',            // Accent color for CTAs and highlights
      light: '#ff5983',
      dark: '#9a0036',
    },
    background: {
      default: '#f5f5f5',         // Light gray background
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.125rem',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,              // Consistent border radius
  },
});

/**
 * ============================================================================
 * PROTECTED ROUTE COMPONENT
 * ============================================================================
 * Wrapper component that enforces authentication for protected pages
 */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
      >
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

/**
 * Main App Component
 */
const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </BrowserRouter>
          <Toaster position="top-right" />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
