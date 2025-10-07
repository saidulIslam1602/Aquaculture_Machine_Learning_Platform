/**
 * Dashboard Page Component
 * 
 * Main dashboard with metrics, charts, and system overview.
 * 
 * Industry Standards:
 *   - Component composition
 *   - React hooks for state management
 *   - Material-UI for consistent design
 *   - Real-time data updates
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
} from '@mui/material';
import {
  TrendingUp,
  Speed,
  CheckCircle,
  Assessment,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { DashboardStats, MetricData } from '../types';

/**
 * Metric Card Component Props
 */
interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

/**
 * Metric Card Component
 * 
 * Displays a single metric with icon and value.
 * 
 * @param props - Component props
 * @returns Metric card component
 */
const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color }) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="body2">
            {title}
          </Typography>
          <Typography variant="h4">{value}</Typography>
        </Box>
        <Box sx={{ color, fontSize: 48 }}>{icon}</Box>
      </Box>
    </CardContent>
  </Card>
);

/**
 * Dashboard Component
 * 
 * Main dashboard page with system metrics and visualizations.
 * 
 * @returns Dashboard page component
 */
const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    total_predictions: 0,
    active_tasks: 0,
    model_accuracy: 0,
    avg_inference_time_ms: 0,
    predictions_today: 0,
    error_rate: 0,
  });

  const [metricsData, setMetricsData] = useState<MetricData[]>([]);

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        // TODO: Fetch real stats from API
        // For now, use mock data
        setStats({
          total_predictions: 15420,
          active_tasks: 8,
          model_accuracy: 0.945,
          avg_inference_time_ms: 45.2,
          predictions_today: 342,
          error_rate: 0.012,
        });

        // Generate mock metrics data
        const mockData: MetricData[] = Array.from({ length: 24 }, (_, i) => ({
          timestamp: Date.now() - (23 - i) * 3600000,
          value: Math.random() * 100 + 50,
        }));
        setMetricsData(mockData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      }
    };

    fetchData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Metric Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Predictions"
            value={stats.total_predictions.toLocaleString()}
            icon={<Assessment />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Tasks"
            value={stats.active_tasks}
            icon={<TrendingUp />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Model Accuracy"
            value={`${(stats.model_accuracy * 100).toFixed(1)}%`}
            icon={<CheckCircle />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Inference Time"
            value={`${stats.avg_inference_time_ms.toFixed(1)}ms`}
            icon={<Speed />}
            color="#9c27b0"
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Predictions Over Time
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metricsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(ts: number) => new Date(ts).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(ts: number) => new Date(ts).toLocaleString()}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#1976d2"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="textSecondary">
                Predictions Today
              </Typography>
              <Typography variant="h5">{stats.predictions_today}</Typography>

              <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                Error Rate
              </Typography>
              <Typography variant="h5">
                {(stats.error_rate * 100).toFixed(2)}%
              </Typography>

              <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                Status
              </Typography>
              <Typography variant="h5" color="success.main">
                Healthy
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
