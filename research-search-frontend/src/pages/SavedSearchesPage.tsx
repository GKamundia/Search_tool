import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const SavedSearchesPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Saved Searches
      </Typography>
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Your saved searches will appear here. This feature is coming soon.
        </Typography>
      </Paper>
    </Box>
  );
};

export default SavedSearchesPage;