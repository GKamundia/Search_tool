import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { Link } from 'react-router-dom';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import HomeIcon from '@mui/icons-material/Home';

const NotFound: React.FC = () => {
  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
      <Paper sx={{ p: 4, maxWidth: 500, textAlign: 'center' }}>
        <ErrorOutlineIcon sx={{ fontSize: 60, color: 'error.main', mb: 2 }} />
        
        <Typography variant="h4" component="h1" gutterBottom>
          404: Page Not Found
        </Typography>
        
        <Typography variant="body1" paragraph>
          The page you are looking for does not exist or has been moved.
        </Typography>
        
        <Button 
          component={Link} 
          to="/" 
          variant="contained" 
          color="primary"
          startIcon={<HomeIcon />}
        >
          Return to Dashboard
        </Button>
      </Paper>
    </Box>
  );
};

export default NotFound;