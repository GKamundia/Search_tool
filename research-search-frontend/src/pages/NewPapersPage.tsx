import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const NewPapersPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        New Papers
      </Typography>
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Newly discovered papers from your saved searches will appear here. This feature is coming soon.
        </Typography>
      </Paper>
    </Box>
  );
};

export default NewPapersPage;