import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Chip,
  Button,
  Divider
} from '@mui/material';
import DatabaseResults from './DatabaseResults';
import { SearchResults } from '../../services/searchService';
import SaveIcon from '@mui/icons-material/Save';
import DownloadIcon from '@mui/icons-material/Download';

interface ResultsContainerProps {
  results: SearchResults;
  query: string;
}

const ResultsContainer: React.FC<ResultsContainerProps> = ({
  results,
  query
}) => {
  const [activeTab, setActiveTab] = useState(0);

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

  return (
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
          >
            Save Search
          </Button>
          <Button 
            startIcon={<DownloadIcon />} 
            variant="outlined"
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
  );
};

export default ResultsContainer;