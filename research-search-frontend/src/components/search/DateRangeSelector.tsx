import React from 'react';
import {
  TextField,
  Grid,
  Paper
} from '@mui/material';

interface DateRangeSelectorProps {
  startYear: string;
  endYear: string;
  onStartYearChange: (value: string) => void;
  onEndYearChange: (value: string) => void;
}

const DateRangeSelector: React.FC<DateRangeSelectorProps> = ({
  startYear,
  endYear,
  onStartYearChange,
  onEndYearChange
}) => {
  const currentYear = new Date().getFullYear();
  
  const validateYear = (value: string): boolean => {
    if (value === '') return true;
    const year = parseInt(value, 10);
    return !isNaN(year) && year >= 1800 && year <= currentYear;
  };

  const handleStartYearChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    if (validateYear(value)) {
      onStartYearChange(value);
    }
  };

  const handleEndYearChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    if (validateYear(value)) {
      onEndYearChange(value);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <TextField
            fullWidth
            label="From Year"
            value={startYear}
            onChange={handleStartYearChange}
            size="small"
            placeholder="e.g., 2010"
            inputProps={{ maxLength: 4 }}
            error={startYear !== '' && !validateYear(startYear)}
            helperText={startYear !== '' && !validateYear(startYear) ? 'Invalid year' : ''}
          />
        </Grid>
        <Grid item xs={6}>
          <TextField
            fullWidth
            label="To Year"
            value={endYear}
            onChange={handleEndYearChange}
            size="small"
            placeholder={`e.g., ${currentYear}`}
            inputProps={{ maxLength: 4 }}
            error={endYear !== '' && !validateYear(endYear)}
            helperText={endYear !== '' && !validateYear(endYear) ? 'Invalid year' : ''}
          />
        </Grid>
      </Grid>
    </Paper>
  );
};

export default DateRangeSelector;