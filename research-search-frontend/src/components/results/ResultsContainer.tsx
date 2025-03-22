import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Chip,
  Button,
  Divider,
  Snackbar,
  Alert
} from '@mui/material';
import DatabaseResults from './DatabaseResults';
import { SearchResults } from '../../services/searchService';
import SaveIcon from '@mui/icons-material/Save';
import DownloadIcon from '@mui/icons-material/Download';
import SaveSearchModal from '../search/SaveSearchModal';

interface ResultsContainerProps {
  results: SearchResults;
  query: string;
  searchParams?: {
    maxResults: number;
    startYear?: string;
    endYear?: string;
    databases: string[];
  };
}

const ResultsContainer: React.FC<ResultsContainerProps> = ({
  results,
  query,
  searchParams
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success'
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Calculate total results
  const totalResults = Object.values(results).reduce(
    (sum, dbResults) => sum + (dbResults?.length || 0),
    0
  );

  const tabs = [
    { id: 'all', label: `All Results (${totalResults})` },
    { id: 'pubmed', label: `PubMed (${results.pubmed?.length || 0})` },
    { id: 'arxiv', label: `arXiv (${results.arxiv?.length || 0})` },
    { id: 'gim', label: `GIM (${results.gim?.length || 0})` }
  ];

  const handleExport = () => {
    // Open export URL in new tab
    window.open('/export', '_blank');
  };

  const handleSaveSearch = () => {
    setSaveModalOpen(true);
  };

  const handleSaveSuccess = () => {
    setNotification({
      open: true,
      message: 'Search saved successfully',
      severity: 'success'
    });
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" component="h2">
            Search Results
          </Typography>
          <Box>
            <Button 
              startIcon={<SaveIcon />} 
              variant="outlined"
              sx={{ mr: 1 }}
              onClick={handleSaveSearch}
            >
              Save Search
            </Button>
            <Button 
              startIcon={<DownloadIcon />} 
              variant="outlined"
              onClick={handleExport}
            >
              Export
            </Button>
          </Box>
        </Box>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Query: <Chip label={query} size="small" />
          </Typography>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            aria-label="search results tabs"
          >
            {tabs.map((tab, index) => (
              <Tab key={tab.id} label={tab.label} id={`tab-${tab.id}`} />
            ))}
          </Tabs>
        </Box>
        
        {activeTab === 0 && (
          <Box>
            {/* Show all results when "All Results" tab is selected */}
            {results.pubmed && results.pubmed.length > 0 && (
              <Box mb={4}>
                <Typography variant="h6" gutterBottom>PubMed</Typography>
                <DatabaseResults results={results.pubmed} database="pubmed" />
              </Box>
            )}
            
            {results.arxiv && results.arxiv.length > 0 && (
              <Box mb={4}>
                <Typography variant="h6" gutterBottom>arXiv</Typography>
                <DatabaseResults results={results.arxiv} database="arxiv" />
              </Box>
            )}
            
            {results.gim && results.gim.length > 0 && (
              <Box mb={4}>
                <Typography variant="h6" gutterBottom>GIM</Typography>
                <DatabaseResults results={results.gim} database="gim" />
              </Box>
            )}
            
            {totalResults === 0 && (
              <Typography align="center" color="text.secondary" sx={{ py: 4 }}>
                No results found. Try different search terms or databases.
              </Typography>
            )}
          </Box>
        )}
        
        {activeTab === 1 && results.pubmed && (
          <DatabaseResults results={results.pubmed} database="pubmed" />
        )}
        
        {activeTab === 2 && results.arxiv && (
          <DatabaseResults results={results.arxiv} database="arxiv" />
        )}
        
        {activeTab === 3 && results.gim && (
          <DatabaseResults results={results.gim} database="gim" />
        )}
      </Paper>
      
      {searchParams && (
        <SaveSearchModal
          open={saveModalOpen}
          onClose={() => setSaveModalOpen(false)}
          searchParams={{
            query,
            databases: searchParams.databases,
            maxResults: searchParams.maxResults,
            startYear: searchParams.startYear,
            endYear: searchParams.endYear
          }}
          onSuccess={handleSaveSuccess}
        />
      )}
      
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default ResultsContainer;