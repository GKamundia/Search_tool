// src/pages/SearchPage.tsx
import React, { useState } from 'react';
import { Box, Typography, Alert, CircularProgress } from '@mui/material';
import SearchForm from '../components/search/SearchForm';
import ResultsContainer from '../components/results/ResultsContainer';
import searchService, { SearchParams, SearchResults } from '../services/searchService';

const SearchPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResults | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const handleSearch = async (params: SearchParams) => {
    try {
      setLoading(true);
      setError(null);
      const response = await searchService.performSearch(params);
      setResults(response.results);
      setSearchQuery(response.query || params.terms.join(' ')); 
    } catch (err: any) {
      setError(err.message || 'An error occurred during search');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Advanced Search
      </Typography>
      
      <SearchForm onSearch={handleSearch} />
      
      {loading && (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      
      {results && !loading && (
        <ResultsContainer 
          results={results} 
          query={searchQuery} 
        />
      )}
    </Box>
  );
};

export default SearchPage;