import React from 'react';
import {
  FormGroup,
  FormControlLabel,
  Checkbox,
  Box,
  Tooltip,
  Paper
} from '@mui/material';

interface DatabaseSelectorProps {
  selectedDatabases: string[];
  onChange: (databases: string[]) => void;
}

interface Database {
  id: string;
  name: string;
  description: string;
  icon?: React.ReactNode;
}

const DatabaseSelector: React.FC<DatabaseSelectorProps> = ({
  selectedDatabases,
  onChange
}) => {
  const databases: Database[] = [
    {
      id: 'pubmed',
      name: 'PubMed',
      description: 'Biomedical literature from MEDLINE, life science journals, and online books'
    },
    {
      id: 'arxiv',
      name: 'arXiv',
      description: 'Open access archive for scholarly articles in physics, mathematics, computer science, and more'
    },
    {
      id: 'gim',
      name: 'GIM',
      description: 'Generic information management database for academic research'
    }
  ];

  const handleChange = (databaseId: string) => {
    if (selectedDatabases.includes(databaseId)) {
      // Remove database if already selected
      onChange(selectedDatabases.filter(id => id !== databaseId));
    } else {
      // Add database if not selected
      onChange([...selectedDatabases, databaseId]);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <FormGroup>
        {databases.map(db => (
          <Tooltip key={db.id} title={db.description} placement="right">
            <FormControlLabel
              control={
                <Checkbox
                  checked={selectedDatabases.includes(db.id)}
                  onChange={() => handleChange(db.id)}
                  name={db.id}
                />
              }
              label={db.name}
            />
          </Tooltip>
        ))}
      </FormGroup>
      {selectedDatabases.length === 0 && (
        <Box sx={{ color: 'error.main', mt: 1, fontSize: '0.875rem' }}>
          Please select at least one database
        </Box>
      )}
    </Paper>
  );
};

export default DatabaseSelector;