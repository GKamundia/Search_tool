import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const SettingsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Application settings will appear here. This feature is coming soon.
        </Typography>
      </Paper>
    </Box>
  );
};

export default SettingsPage;