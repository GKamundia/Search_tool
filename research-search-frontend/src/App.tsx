import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import MainLayout from './components/layout/MainLayout';

// Lazy-load page components
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const SearchPage = React.lazy(() => import('./pages/SearchPage'));
const SavedSearchesPage = React.lazy(() => import('./pages/SavedSearchesPage'));
const NewPapersPage = React.lazy(() => import('./pages/NewPapersPage'));
const SettingsPage = React.lazy(() => import('./pages/SettingsPage'));
const HelpPage = React.lazy(() => import('./pages/HelpPage'));
const NotFound = React.lazy(() => import('./pages/NotFound'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={
        <Box 
          sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center',
            height: '100vh' 
          }}
        >
          <CircularProgress />
        </Box>
      }>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="saved-searches" element={<SavedSearchesPage />} />
            <Route path="new-papers" element={<NewPapersPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="help" element={<HelpPage />} />
            <Route path="404" element={<NotFound />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
