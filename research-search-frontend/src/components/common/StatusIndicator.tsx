import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, Chip, CircularProgress } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import api from '../../services/api';

interface StatusData {
  status: string;
  version: string;
  database_status: string;
}

const StatusIndicator: React.FC = () => {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        const response = await api.get<StatusData>('/status');
        setStatus(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to connect to API');
        console.error('Error fetching status:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, []);

  return (
    <Paper
      elevation={1}
      sx={{
        p: 3,
        borderRadius: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      <Typography variant="h5" component="h2" fontWeight="500">
        System Status
      </Typography>
      
      {loading ? (
        <Box display="flex" alignItems="center" gap={2}>
          <CircularProgress size={20} />
          <Typography>Checking connection...</Typography>
        </Box>
      ) : error ? (
        <Box display="flex" alignItems="center" gap={2}>
          <ErrorOutlineIcon color="error" />
          <Typography color="error.main">{error}</Typography>
        </Box>
      ) : (
        <Box display="flex" flexDirection="column" gap={1}>
          <Box display="flex" alignItems="center" gap={2}>
            <CheckCircleOutlineIcon color="success" />
            <Typography>API Connected</Typography>
            <Chip 
              label={status?.status || 'Unknown'} 
              color="primary" 
              size="small" 
              variant="outlined"
            />
          </Box>
          <Box display="flex" gap={2} mt={1}>
            <Typography variant="body2" color="text.secondary">
              Version: {status?.version || 'Unknown'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Database: {status?.database_status || 'Unknown'}
            </Typography>
          </Box>
        </Box>
      )}
    </Paper>
  );
};

export default StatusIndicator;

