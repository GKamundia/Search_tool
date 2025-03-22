import React, { useState } from 'react';
import { Box, useMediaQuery, useTheme } from '@mui/material';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

const MainLayout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleCloseSidebar = () => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar - permanent on desktop, temporary on mobile */}
      <Sidebar 
        open={sidebarOpen} 
        onClose={handleCloseSidebar} 
        variant={isMobile ? "temporary" : "permanent"} 
      />
      
      {/* Main content area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          width: { sm: `calc(100% - ${sidebarOpen && !isMobile ? 250 : 0}px)` },
          ml: { sm: sidebarOpen && !isMobile ? '250px' : 0 },
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Navbar toggleSidebar={toggleSidebar} />
        
        {/* Main content - padding accounts for navbar height */}
        <Box
          sx={{
            flexGrow: 1,
            p: 3,
            mt: 8, // Space for navbar
            backgroundColor: theme.palette.background.default,
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};

export default MainLayout;

