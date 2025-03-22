import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Divider,
  Link as MuiLink
} from '@mui/material';
import FilterAltIcon from '@mui/icons-material/FilterAlt';
import InsertLinkIcon from '@mui/icons-material/InsertLink';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import savedSearchService, { NewPaper, SavedSearch } from '../services/savedSearchService';

const NewPapersPage: React.FC = () => {
  const [papers, setPapers] = useState<NewPaper[]>([]);
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [selectedSearchId, setSelectedSearchId] = useState<string>('');
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [markingRead, setMarkingRead] = useState<number | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch saved searches for filter dropdown
      const searchesData = await savedSearchService.getSavedSearches();
      setSearches(searchesData);
      
      // Fetch papers with filters
      const filters: { search_id?: number; database?: string } = {};
      if (selectedSearchId) {
        filters.search_id = parseInt(selectedSearchId, 10);
      }
      if (selectedDatabase) {
        filters.database = selectedDatabase;
      }
      
      const papersData = await savedSearchService.getNewPapers(filters);
      setPapers(papersData);
    } catch (err: any) {
      setError(err.message || 'Failed to load new papers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedSearchId, selectedDatabase]);

  const handleSearchChange = (event: SelectChangeEvent) => {
    setSelectedSearchId(event.target.value);
  };

  const handleDatabaseChange = (event: SelectChangeEvent) => {
    setSelectedDatabase(event.target.value);
  };

  const handleMarkAsRead = async (paperId: number) => {
    try {
      setMarkingRead(paperId);
      await savedSearchService.markAsRead(paperId);
      // Remove the paper from the list
      setPapers(papers.filter(paper => paper.id !== paperId));
    } catch (err: any) {
      setError(err.message || 'Failed to mark paper as read');
    } finally {
      setMarkingRead(null);
    }
  };

  const getDatabaseColor = (database: string) => {
    switch (database.toLowerCase()) {
      case 'pubmed':
        return 'primary';
      case 'arxiv':
        return 'secondary';
      case 'gim':
        return 'success';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          New Papers
        </Typography>
      </Box>
      
      {/* Filter Form */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          <FilterAltIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Filter Options
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel id="saved-search-label">Saved Search</InputLabel>
              <Select
                labelId="saved-search-label"
                value={selectedSearchId}
                label="Saved Search"
                onChange={handleSearchChange}
              >
                <MenuItem value="">All Saved Searches</MenuItem>
                {searches.map((search) => (
                  <MenuItem key={search.id} value={search.id.toString()}>
                    {search.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel id="database-label">Database</InputLabel>
              <Select
                labelId="database-label"
                value={selectedDatabase}
                label="Database"
                onChange={handleDatabaseChange}
              >
                <MenuItem value="">All Databases</MenuItem>
                <MenuItem value="pubmed">PubMed</MenuItem>
                <MenuItem value="arxiv">arXiv</MenuItem>
                <MenuItem value="gim">GIM</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>
      
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      ) : papers.length === 0 ? (
        <Alert severity="info">
          No new papers found. Save searches and wait for new papers to be discovered, or run searches manually.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {papers.map((paper) => (
            <Grid item xs={12} key={paper.id}>
              <Card 
                variant="outlined"
                sx={{
                  borderLeft: `4px solid ${
                    paper.database === 'pubmed' ? '#3f51b5' : 
                    paper.database === 'arxiv' ? '#f50057' : '#4caf50'
                  }`,
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box>
                      <Typography variant="h6" component="h3" gutterBottom>
                        {paper.title}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {paper.authors}
                      </Typography>
                      
                      <Box sx={{ mt: 1, mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip 
                          label={paper.database.toUpperCase()} 
                          size="small" 
                          color={getDatabaseColor(paper.database)}
                        />
                        
                        {paper.publication_date && (
                          <Chip 
                            label={new Date(paper.publication_date).toLocaleDateString()} 
                            size="small" 
                            variant="outlined" 
                          />
                        )}
                        
                        {paper.saved_search_id && (
                          <Chip 
                            label={searches.find(s => s.id === paper.saved_search_id)?.name || `Search #${paper.saved_search_id}`} 
                            size="small" 
                            variant="outlined" 
                          />
                        )}
                      </Box>
                    </Box>
                    
                    <Button
                      variant="outlined"
                      size="small"
                      color="success"
                      startIcon={<CheckCircleOutlineIcon />}
                      disabled={markingRead === paper.id}
                      onClick={() => handleMarkAsRead(paper.id)}
                    >
                      {markingRead === paper.id ? (
                        <CircularProgress size={16} />
                      ) : (
                        'Mark Read'
                      )}
                    </Button>
                  </Box>
                  
                  {paper.abstract && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="body2">
                        {paper.abstract.length > 300 ? 
                          `${paper.abstract.substring(0, 300)}...` : 
                          paper.abstract
                        }
                      </Typography>
                    </>
                  )}
                  
                  {paper.url && (
                    <Box sx={{ mt: 2 }}>
                      <MuiLink 
                        href={paper.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                      >
                        <InsertLinkIcon fontSize="small" />
                        View Source
                      </MuiLink>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default NewPapersPage;