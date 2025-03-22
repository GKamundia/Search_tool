import React from 'react';
import { Box, Typography, Grid, Paper } from '@mui/material';
import StatusIndicator from '../components/common/StatusIndicator';

const Dashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      <Typography variant="body1" paragraph>
        Welcome to the Academic Search Portal. This dashboard provides an overview of your searches and new papers.
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <StatusIndicator />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Recent Activity</Typography>
            <Typography variant="body1">
              No recent activity to display.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;