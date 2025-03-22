import React from 'react';
import { Box, Typography, Paper, Tabs, Tab } from '@mui/material';
import { SearchParams } from '../../services/searchService';

interface QueryPreviewProps {
  searchParams: SearchParams;
}

const QueryPreview: React.FC<QueryPreviewProps> = ({ searchParams }) => {
  const [activeTab, setActiveTab] = React.useState(0);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Build queries for each database
  const buildPubMedQuery = (): string => {
    if (searchParams.terms.length === 0) return '';
    
    const queryParts: string[] = [];
    
    searchParams.terms.forEach((term, index) => {
      if (term.trim()) {
        const field = searchParams.fields[index] || '';
        let fieldMapping = '';
        
        // Map field values to PubMed syntax
        switch (field) {
          case 'title':
            fieldMapping = '[Title]';
            break;
          case 'title_abstract':
            fieldMapping = '[Title/Abstract]';
            break;
          case 'abstract':
            fieldMapping = '[Abstract]';
            break;
          case 'author':
            fieldMapping = '[Author]';
            break;
          case 'journal':
            fieldMapping = '[Journal]';
            break;
          case 'keyword':
            fieldMapping = '[MeSH Terms]';
            break;
          case 'mesh':
            fieldMapping = '[MeSH Terms]';
            break;
          default:
            fieldMapping = '';
        }
        
        queryParts.push(`(${term}${fieldMapping})`);
        
        // Add operator if not the last term
        if (index < searchParams.terms.length - 1) {
          queryParts.push(searchParams.operators[index] || 'AND');
        }
      }
    });
    
    // Add date filter if provided
    if (searchParams.startYear && searchParams.endYear) {
      queryParts.push(`AND (${searchParams.startYear}:${searchParams.endYear}[dp])`);
    }
    
    return queryParts.join(' ');
  };

  const buildArXivQuery = (): string => {
    if (searchParams.terms.length === 0) return '';
    
    const queryParts: string[] = [];
    
    searchParams.terms.forEach((term, index) => {
      if (term.trim()) {
        const field = searchParams.fields[index] || '';
        let fieldMapping = '';
        
        // Map field values to arXiv syntax
        switch (field) {
          case 'title':
            fieldMapping = 'ti:';
            break;
          case 'title_abstract':
            fieldMapping = 'all:';
            break;
          case 'abstract':
            fieldMapping = 'abs:';
            break;
          case 'author':
            fieldMapping = 'au:';
            break;
          case 'journal':
            fieldMapping = 'jr:';
            break;
          default:
            fieldMapping = '';
        }
        
        queryParts.push(fieldMapping ? `${fieldMapping}"${term}"` : term);
        
        // Add operator if not the last term
        if (index < searchParams.terms.length - 1) {
          queryParts.push(searchParams.operators[index] || 'AND');
        }
      }
    });
    
    // Add date filter if provided
    if (searchParams.startYear && searchParams.endYear) {
      queryParts.push(` AND submittedDate:[${searchParams.startYear}0101 TO ${searchParams.endYear}1231]`);
    }
    
    return queryParts.join(' ');
  };

  const buildGIMQuery = (): string => {
    if (searchParams.terms.length === 0) return '';
    
    const queryParts: string[] = [];
    
    searchParams.terms.forEach((term, index) => {
      if (term.trim()) {
        const field = searchParams.fields[index] || '';
        let fieldMapping = '';
        
        // Map field values to GIM syntax
        switch (field) {
          case 'title':
            fieldMapping = 'title:';
            break;
          case 'title_abstract':
            // GIM might use a different approach for title+abstract
            fieldMapping = 'title_abstract:';
            break;
          case 'abstract':
            fieldMapping = 'abstract:';
            break;
          case 'author':
            fieldMapping = 'author:';
            break;
          case 'journal':
            fieldMapping = 'source:';
            break;
          case 'keyword':
            fieldMapping = 'keyword:';
            break;
          default:
            fieldMapping = '';
        }
        
        queryParts.push(field ? `${fieldMapping}"${term}"` : term);
        
        // Add operator if not the last term
        if (index < searchParams.terms.length - 1) {
          queryParts.push(searchParams.operators[index] || 'AND');
        }
      }
    });
    
    // Add date filter if provided
    if (searchParams.startYear && searchParams.endYear) {
      queryParts.push(` AND year:${searchParams.startYear}-${searchParams.endYear}`);
    }
    
    return queryParts.join(' ');
  };

  // Return empty component if no search terms
  if (searchParams.terms.length === 0 || searchParams.terms.every(term => !term.trim())) {
    return null;
  }

  return (
    <Paper sx={{ p: 2, mt: 2 }}>
      <Typography variant="subtitle1" gutterBottom>
        Query Preview
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="PubMed" disabled={!searchParams.databases.includes('pubmed')} />
          <Tab label="arXiv" disabled={!searchParams.databases.includes('arxiv')} />
          <Tab label="GIM" disabled={!searchParams.databases.includes('gim')} />
        </Tabs>
      </Box>
      
      <Box sx={{ p: 2, bgcolor: 'grey.100', mt: 2, borderRadius: 1, fontFamily: 'monospace', overflowX: 'auto' }}>
        <Typography component="pre" sx={{ m: 0, overflowWrap: 'break-word' }}>
          {activeTab === 0 && buildPubMedQuery()}
          {activeTab === 1 && buildArXivQuery()}
          {activeTab === 2 && buildGIMQuery()}
        </Typography>
      </Box>
    </Paper>
  );
};

export default QueryPreview;