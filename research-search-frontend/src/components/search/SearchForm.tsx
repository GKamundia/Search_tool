import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Button, 
  Typography, 
  Grid,
  Divider
} from '@mui/material';
import SearchTermRow from './SearchTermRow';
import DatabaseSelector from './DatabaseSelector';
import DateRangeSelector from './DateRangeSelector';
import ResultsLimitInput from './ResultsLimitInput';
import QueryPreview from './QueryPreview';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import { SearchParams } from '../../services/searchService';

interface SearchFormProps {
  onSearch: (params: SearchParams) => void;
}

const SearchForm: React.FC<SearchFormProps> = ({ onSearch }) => {
  const [terms, setTerms] = useState<string[]>(['']);
  const [operators, setOperators] = useState<string[]>(['AND']);
  const [fields, setFields] = useState<string[]>(['']);
  const [databases, setDatabases] = useState<string[]>(['pubmed', 'arxiv', 'gim']);
  const [startYear, setStartYear] = useState<string>('');
  const [endYear, setEndYear] = useState<string>('');
  const [maxResults, setMaxResults] = useState<number>(50);
  
  // Create combined search params object for preview
  const [searchParams, setSearchParams] = useState<SearchParams>({
    terms: [],
    operators: [],
    fields: [],
    databases: [],
    maxResults: 50
  });
  
  // Update search params whenever form inputs change
  useEffect(() => {
    setSearchParams({
      terms,
      operators,
      fields,
      databases,
      startYear,
      endYear,
      maxResults
    });
  }, [terms, operators, fields, databases, startYear, endYear, maxResults]);

  const handleAddTerm = () => {
    setTerms([...terms, '']);
    setOperators([...operators, 'AND']);
    setFields([...fields, '']);
  };

  const handleRemoveTerm = (index: number) => {
    const newTerms = [...terms];
    const newOperators = [...operators];
    const newFields = [...fields];

    newTerms.splice(index, 1);
    newOperators.splice(index, 1);
    newFields.splice(index, 1);

    setTerms(newTerms);
    setOperators(newOperators);
    setFields(newFields);
  };

  const handleTermChange = (index: number, value: string) => {
    const newTerms = [...terms];
    newTerms[index] = value;
    setTerms(newTerms);
  };

  const handleOperatorChange = (index: number, value: string) => {
    const newOperators = [...operators];
    newOperators[index] = value;
    setOperators(newOperators);
  };

  const handleFieldChange = (index: number, value: string) => {
    const newFields = [...fields];
    newFields[index] = value;
    setFields(newFields);
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // Filter out empty terms
    const validTermIndices = terms
      .map((term, index) => (term.trim() !== '' ? index : -1))
      .filter(index => index !== -1);
    
    const searchParams: SearchParams = {
      terms: validTermIndices.map(i => terms[i]),
      operators: validTermIndices.map(i => operators[i]),
      fields: validTermIndices.map(i => fields[i]),
      databases,
      startYear: startYear || undefined,
      endYear: endYear || undefined,
      maxResults
    };
    
    onSearch(searchParams);
  };

  return (
    <Paper component="form" onSubmit={handleSubmit} sx={{ p: 3, mb: 4 }}>
      <Typography variant="h6" gutterBottom>
        Build Your Search Query
      </Typography>
      
      <Box sx={{ mb: 3 }}>
        {terms.map((term, index) => (
          <SearchTermRow
            key={index}
            index={index}
            term={term}
            operator={operators[index]}
            field={fields[index]}
            isFirst={index === 0}
            onTermChange={handleTermChange}
            onOperatorChange={handleOperatorChange}
            onFieldChange={handleFieldChange}
            onRemove={() => handleRemoveTerm(index)}
          />
        ))}
        
        <Button
          startIcon={<AddIcon />}
          onClick={handleAddTerm}
          variant="text"
          sx={{ mt: 1 }}
        >
          Add search term
        </Button>
      </Box>
      
      {/* Query Preview */}
      <QueryPreview searchParams={searchParams} />
      
      <Divider sx={{ my: 3 }} />
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle1" gutterBottom>
            Select Databases
          </Typography>
          <DatabaseSelector
            selectedDatabases={databases}
            onChange={setDatabases}
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle1" gutterBottom>
            Publication Date Range
          </Typography>
          <DateRangeSelector
            startYear={startYear}
            endYear={endYear}
            onStartYearChange={setStartYear}
            onEndYearChange={setEndYear}
          />
          
          <Box mt={3}>
            <Typography variant="subtitle1" gutterBottom>
              Maximum Results
            </Typography>
            <ResultsLimitInput
              value={maxResults}
              onChange={setMaxResults}
            />
          </Box>
        </Grid>
      </Grid>
      
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Button
          type="submit"
          variant="contained"
          color="primary"
          size="large"
          startIcon={<SearchIcon />}
        >
          Search
        </Button>
      </Box>
    </Paper>
  );
};

export default SearchForm;