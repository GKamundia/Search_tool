import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const HelpPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Help & Documentation
      </Typography>
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          User documentation and help resources will appear here. This feature is coming soon.
        </Typography>
      </Paper>
    </Box>
  );
};

export default HelpPage;