import React from 'react';
import {
  TextField,
  Slider,
  Box,
  Paper
} from '@mui/material';

interface ResultsLimitInputProps {
  value: number;
  onChange: (value: number) => void;
}

const ResultsLimitInput: React.FC<ResultsLimitInputProps> = ({
  value,
  onChange
}) => {
  const handleSliderChange = (event: Event, newValue: number | number[]) => {
    onChange(newValue as number);
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(event.target.value);
    if (!isNaN(newValue) && newValue >= 10 && newValue <= 200) {
      onChange(newValue);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Slider
          value={value}
          onChange={handleSliderChange}
          aria-labelledby="results-limit-slider"
          min={10}
          max={200}
          step={10}
          sx={{ flex: 1, mr: 2 }}
        />
        <TextField
          value={value}
          onChange={handleInputChange}
          type="number"
          inputProps={{
            min: 10,
            max: 200,
            step: 10,
          }}
          sx={{ width: '80px' }}
          size="small"
          variant="outlined"
        />
      </Box>
    </Paper>
  );
};

export default ResultsLimitInput;