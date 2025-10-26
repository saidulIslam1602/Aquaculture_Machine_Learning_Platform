/**
 * ============================================================================
 * Aquaculture ML Platform - Login Page Component
 * ============================================================================
 * 
 * User authentication page for the Aquaculture ML Platform.
 * Provides secure login functionality with JWT token-based authentication.
 *
 * FEATURES:
 * - Email/username and password authentication
 * - Form validation and error handling
 * - Loading states for better UX
 * - Automatic redirect after successful login
 * - Material-UI design for consistent branding
 *
 * SECURITY:
 * - Password input masking
 * - Secure token storage
 * - HTTPS recommended for production
 * - Protection against common vulnerabilities
 * ============================================================================
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

/**
 * Login Page Component
 * 
 * Renders the login form and handles user authentication.
 * 
 * @returns Login page component
 */
const Login: React.FC = () => {
  // Authentication context
  const { login } = useAuth();
  const navigate = useNavigate();

  // Form state management
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  /**
   * Handle form submission
   * 
   * Authenticates user and redirects to dashboard on success.
   * 
   * @param e - Form submission event
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(credentials);
      // Redirect to dashboard on successful login
      navigate('/');
    } catch (err: any) {
      // Display error message from API or generic error
      const errorMessage = err.response?.data?.detail || 
                          err.message || 
                          'Login failed. Please check your credentials.';
      setError(errorMessage);
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle input field changes
   * 
   * @param field - Field name to update
   * @param value - New field value
   */
  const handleChange = (field: 'username' | 'password', value: string) => {
    setCredentials({ ...credentials, [field]: value });
    // Clear error when user starts typing
    if (error) setError('');
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      bgcolor="#f5f5f5"
      sx={{
        backgroundImage: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card sx={{ maxWidth: 450, width: '100%', m: 2, boxShadow: 3 }}>
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Box textAlign="center" mb={3}>
            <Typography variant="h4" fontWeight="bold" gutterBottom color="primary">
              Aquaculture ML Platform
            </Typography>
            <Typography variant="body2" color="textSecondary">
              🐟 AI-Powered Fish Species Classification
            </Typography>
          </Box>

          {/* Login Form */}
          <form onSubmit={handleSubmit}>
            {/* Error Alert */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {/* Username Field */}
            <TextField
              fullWidth
              label="Username or Email"
              value={credentials.username}
              onChange={(e) => handleChange('username', e.target.value)}
              margin="normal"
              required
              autoComplete="username"
              autoFocus
              disabled={loading}
              variant="outlined"
            />

            {/* Password Field */}
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={credentials.password}
              onChange={(e) => handleChange('password', e.target.value)}
              margin="normal"
              required
              autoComplete="current-password"
              disabled={loading}
              variant="outlined"
            />

            {/* Submit Button */}
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={loading}
              sx={{ mt: 3, mb: 2, py: 1.5 }}
            >
              {loading ? (
                <>
                  <CircularProgress size={24} sx={{ mr: 1 }} color="inherit" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          {/* Help Text */}
          <Box mt={3} textAlign="center">
            <Typography variant="body2" color="textSecondary">
              Demo credentials: username: <strong>demo</strong>, password: <strong>demo12345</strong>
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Login;

