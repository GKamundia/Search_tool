import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Collapse,
  Grid,
  Divider,
  Link
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import BookmarkBorderIcon from '@mui/icons-material/BookmarkBorder';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import InsertLinkIcon from '@mui/icons-material/InsertLink';

interface ResultItem {
  id: string;
  title: string;
  authors?: string[] | string;
  abstract?: string;
  journal?: string;
  year?: string;
  url?: string;
  doi?: string;
  database: string;
  keywords?: string[];
}

interface DatabaseResultsProps {
  results: any[]; // Should be ResultItem[], but using any[] for flexibility with API
  database: string;
}

const DatabaseResults: React.FC<DatabaseResultsProps> = ({
  results,
  database
}) => {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [readIds, setReadIds] = useState<Set<string>>(new Set());

  const formatAuthors = (authors: any): string => {
    if (!authors) return 'Unknown authors';
    
    if (Array.isArray(authors)) {
      return authors.join(', ');
    }
    
    if (typeof authors === 'string') {
      return authors;
    }
    
    return 'Unknown authors';
  };

  const toggleExpand = (id: string) => {
    const newExpandedIds = new Set(expandedIds);
    if (newExpandedIds.has(id)) {
      newExpandedIds.delete(id);
    } else {
      newExpandedIds.add(id);
    }
    setExpandedIds(newExpandedIds);
  };

  const toggleSaved = (id: string) => {
    const newSavedIds = new Set(savedIds);
    if (newSavedIds.has(id)) {
      newSavedIds.delete(id);
    } else {
      newSavedIds.add(id);
    }
    setSavedIds(newSavedIds);
  };

  const toggleRead = (id: string) => {
    const newReadIds = new Set(readIds);
    if (newReadIds.has(id)) {
      newReadIds.delete(id);
    } else {
      newReadIds.add(id);
    }
    setReadIds(newReadIds);
  };

  if (!results || results.length === 0) {
    return (
      <Typography align="center" color="text.secondary" sx={{ py: 4 }}>
        No results found in this database.
      </Typography>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {results.map((result: any, index: number) => {
        const resultId = result.id || `result-${database}-${index}`;
        const isExpanded = expandedIds.has(resultId);
        const isSaved = savedIds.has(resultId);
        const isRead = readIds.has(resultId);
        
        return (
          <Card 
            key={resultId}
            variant="outlined"
            sx={{
              borderLeft: `4px solid ${
                database === 'pubmed' ? '#3f51b5' : 
                database === 'arxiv' ? '#f50057' : '#4caf50'
              }`,
              opacity: isRead ? 0.7 : 1
            }}
          >
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box flex="1">
                  <Typography variant="h6" component="h3" gutterBottom>
                    {result.title}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {formatAuthors(result.authors)}
                  </Typography>
                  
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {result.journal && (
                      <Chip 
                        label={result.journal} 
                        size="small" 
                        variant="outlined" 
                      />
                    )}
                    
                    {result.year && (
                      <Chip 
                        label={result.year} 
                        size="small" 
                        variant="outlined" 
                      />
                    )}
                    
                    <Chip 
                      label={database.toUpperCase()} 
                      size="small" 
                      color={
                        database === 'pubmed' ? 'primary' : 
                        database === 'arxiv' ? 'secondary' : 'success'
                      }
                    />
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <IconButton 
                    size="small" 
                    onClick={() => toggleRead(resultId)}
                    color={isRead ? 'success' : 'default'}
                    aria-label={isRead ? "Mark as unread" : "Mark as read"}
                  >
                    <CheckCircleOutlineIcon />
                  </IconButton>
                  
                  <IconButton 
                    size="small" 
                    onClick={() => toggleSaved(resultId)}
                    color={isSaved ? 'primary' : 'default'}
                    aria-label={isSaved ? "Remove from saved" : "Save paper"}
                  >
                    {isSaved ? <BookmarkIcon /> : <BookmarkBorderIcon />}
                  </IconButton>
                  
                  <IconButton 
                    size="small" 
                    onClick={() => toggleExpand(resultId)}
                    aria-label={isExpanded ? "Show less" : "Show more"}
                  >
                    {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                </Box>
              </Box>
              
              <Collapse in={isExpanded}>
                <Box sx={{ mt: 2 }}>
                  <Divider sx={{ mb: 2 }} />
                  
                  {result.abstract && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Abstract
                      </Typography>
                      <Typography variant="body2">
                        {result.abstract}
                      </Typography>
                    </Box>
                  )}
                  
                  <Grid container spacing={2}>
                    {result.keywords && result.keywords.length > 0 && (
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" gutterBottom>
                          Keywords
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {result.keywords.map((keyword: string, i: number) => (
                            <Chip key={i} label={keyword} size="small" />
                          ))}
                        </Box>
                      </Grid>
                    )}
                    
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                        {result.url && (
                          <Link 
                            href={result.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                          >
                            <InsertLinkIcon fontSize="small" />
                            View Source
                          </Link>
                        )}
                        
                        {result.doi && (
                          <Link 
                            href={`https://doi.org/${result.doi}`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                          >
                            <InsertLinkIcon fontSize="small" />
                            DOI: {result.doi}
                          </Link>
                        )}
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              </Collapse>
            </CardContent>
          </Card>
        );
      })}
    </Box>
  );
};

export default DatabaseResults;