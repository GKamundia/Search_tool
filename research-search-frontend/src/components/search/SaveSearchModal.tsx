import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  FormControlLabel,
  Checkbox,
  FormGroup,
  FormLabel,
  RadioGroup,
  Radio,
  CircularProgress,
  Alert,
  Typography,
  Box
} from '@mui/material';
import savedSearchService from '../../services/savedSearchService';

interface SaveSearchModalProps {
  open: boolean;
  onClose: () => void;
  searchParams: {
    query: string;
    databases: string[];
    maxResults: number;
    startYear?: string;
    endYear?: string;
  };
  onSuccess: () => void;
}

const SaveSearchModal: React.FC<SaveSearchModalProps> = ({
  open,
  onClose,
  searchParams,
  onSuccess
}) => {
  const [searchName, setSearchName] = useState('');
  const [email, setEmail] = useState('');
  const [frequency, setFrequency] = useState('monthly');
  const [selectedDatabases, setSelectedDatabases] = useState<string[]>([...searchParams.databases]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!searchName.trim()) {
      setError('Search name is required');
      return;
    }
    
    if (selectedDatabases.length === 0) {
      setError('Please select at least one database');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      await savedSearchService.saveSearch({
        search_name: searchName,
        query: searchParams.query,
        databases: selectedDatabases,
        frequency,
        email: email || undefined,
        max_results: searchParams.maxResults,
        start_year: searchParams.startYear,
        end_year: searchParams.endYear
      });
      
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save search');
    } finally {
      setLoading(false);
    }
  };

  const handleDatabaseChange = (db: string) => {
    if (selectedDatabases.includes(db)) {
      setSelectedDatabases(selectedDatabases.filter(d => d !== db));
    } else {
      setSelectedDatabases([...selectedDatabases, db]);
    }
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Save Search for Alerts</DialogTitle>
      
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          <TextField
            label="Search Name"
            value={searchName}
            onChange={(e) => setSearchName(e.target.value)}
            fullWidth
            required
            margin="normal"
            helperText="Give your search a descriptive name"
          />
          
          <TextField
            label="Email Address (optional)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            type="email"
            margin="normal"
            helperText="Receive email notifications when new papers are found"
          />
          
          <Box mt={3}>
            <FormLabel component="legend">Databases to Monitor</FormLabel>
            <FormGroup>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={selectedDatabases.includes('pubmed')}
                    onChange={() => handleDatabaseChange('pubmed')}
                  />
                }
                label="PubMed"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={selectedDatabases.includes('arxiv')}
                    onChange={() => handleDatabaseChange('arxiv')}
                  />
                }
                label="arXiv"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={selectedDatabases.includes('gim')}
                    onChange={() => handleDatabaseChange('gim')}
                  />
                }
                label="GIM"
              />
            </FormGroup>
          </Box>
          
          <Box mt={3}>
            <FormLabel component="legend">Check Frequency</FormLabel>
            <RadioGroup
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
            >
              <FormControlLabel value="daily" control={<Radio />} label="Daily" />
              <FormControlLabel value="weekly" control={<Radio />} label="Weekly" />
              <FormControlLabel value="monthly" control={<Radio />} label="Monthly" />
            </RadioGroup>
          </Box>
          
          <Box mt={2}>
            <Typography variant="body2" color="text.secondary">
              Query: <strong>{searchParams.query}</strong>
            </Typography>
            {searchParams.startYear && searchParams.endYear && (
              <Typography variant="body2" color="text.secondary">
                Date Range: {searchParams.startYear} - {searchParams.endYear}
              </Typography>
            )}
            <Typography variant="body2" color="text.secondary">
              Max Results: {searchParams.maxResults}
            </Typography>
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Saving...' : 'Save Search'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default SaveSearchModal;