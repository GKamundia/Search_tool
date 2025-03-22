import React from 'react';
import {
  Box,
  TextField,
  IconButton,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Grid
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

interface SearchTermRowProps {
  index: number;
  term: string;
  operator: string;
  field: string;
  isFirst: boolean;
  onTermChange: (index: number, value: string) => void;
  onOperatorChange: (index: number, value: string) => void;
  onFieldChange: (index: number, value: string) => void;
  onRemove: () => void;
}

const SearchTermRow: React.FC<SearchTermRowProps> = ({
  index,
  term,
  operator,
  field,
  isFirst,
  onTermChange,
  onOperatorChange,
  onFieldChange,
  onRemove
}) => {
  const fieldOptions = [
    { value: '', label: 'All Fields' },
    { value: 'title', label: 'Title' },
    {value: 'title_abstract', label: 'Title/Abstract'},
    { value: 'abstract', label: 'Abstract' },
    { value: 'author', label: 'Author' },
    { value: 'journal', label: 'Journal/Source' },
    { value: 'keyword', label: 'Keyword' },
    { value: 'mesh', label: 'MeSH Terms' }
  ];

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
      <Grid container spacing={2} alignItems="center">
        {!isFirst && (
          <Grid item xs={12} sm={2}>
            <FormControl fullWidth size="small">
              <InputLabel id={`operator-label-${index}`}>Operator</InputLabel>
              <Select
                labelId={`operator-label-${index}`}
                value={operator}
                label="Operator"
                onChange={(e) => onOperatorChange(index, e.target.value)}
              >
                <MenuItem value="AND">AND</MenuItem>
                <MenuItem value="OR">OR</MenuItem>
                <MenuItem value="NOT">NOT</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        )}
        
        <Grid item xs={12} sm={isFirst ? 6 : 4}>
          <TextField
            fullWidth
            label="Search Term"
            value={term}
            onChange={(e) => onTermChange(index, e.target.value)}
            size="small"
            placeholder="Enter search term"
          />
        </Grid>
        
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth size="small">
            <InputLabel id={`field-label-${index}`}>Field</InputLabel>
            <Select
              labelId={`field-label-${index}`}
              value={field}
              label="Field"
              onChange={(e) => onFieldChange(index, e.target.value)}
            >
              {fieldOptions.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={2}>
          <IconButton 
            onClick={onRemove} 
            disabled={isFirst && term === ''}
            color="error"
            size="small"
          >
            <DeleteIcon />
          </IconButton>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SearchTermRow;