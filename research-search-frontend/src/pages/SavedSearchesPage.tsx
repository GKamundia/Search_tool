import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  IconButton,
  Alert,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Snackbar
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import BugReportIcon from '@mui/icons-material/BugReport';
import PauseIcon from '@mui/icons-material/Pause';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import savedSearchService, { SavedSearch } from '../services/savedSearchService';
import { format } from 'date-fns';

const SavedSearchesPage: React.FC = () => {
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'info' | 'warning' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success'
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [searchToDelete, setSearchToDelete] = useState<number | null>(null);

  const fetchSavedSearches = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await savedSearchService.getSavedSearches();
      setSearches(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load saved searches');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSavedSearches();
  }, []);

  const handleRunSearch = async (searchId: number) => {
    try {
      setActionLoading(searchId);
      const result = await savedSearchService.runSearch(searchId);
      
      if (result.error) {
        showNotification(result.error, 'error');
      } else if (result.success) {
        if (result.new_papers_count > 0) {
          showNotification(
            `Found ${result.new_papers_count} new papers for "${result.search_name}". Check the New Papers page to view them.`,
            'success'
          );
        } else {
          showNotification(`No new papers found for "${result.search_name}".`, 'info');
        }
      }
    } catch (err: any) {
      showNotification(err.message || 'Failed to run search', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleTestAlert = async (searchId: number) => {
    try {
      setActionLoading(searchId);
      const result = await savedSearchService.testAlert(searchId);
      
      if (result.error) {
        showNotification(result.error, 'error');
      } else if (result.success) {
        showNotification(
          `Test completed successfully. Generated ${result.new_papers_count} test papers for "${result.search_name}".`,
          'success'
        );
      }
    } catch (err: any) {
      showNotification(err.message || 'Failed to run test alert', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleSearch = async (searchId: number) => {
    try {
      setActionLoading(searchId);
      await savedSearchService.toggleSearch(searchId);
      
      // Update the state rather than fetching again
      setSearches(searches.map(s => {
        if (s.id === searchId) {
          return { ...s, active: !s.active };
        }
        return s;
      }));
      
      const search = searches.find(s => s.id === searchId);
      const status = search?.active ? 'deactivated' : 'activated';
      showNotification(`Search "${search?.name}" has been ${status}.`, 'success');
    } catch (err: any) {
      showNotification(err.message || 'Failed to toggle search status', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const openDeleteDialog = (searchId: number) => {
    setSearchToDelete(searchId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteSearch = async () => {
    if (!searchToDelete) return;
    
    try {
      setActionLoading(searchToDelete);
      await savedSearchService.deleteSearch(searchToDelete);
      
      // Update state
      const deletedSearch = searches.find(s => s.id === searchToDelete);
      setSearches(searches.filter(s => s.id !== searchToDelete));
      showNotification(`Search "${deletedSearch?.name}" has been deleted.`, 'success');
    } catch (err: any) {
      showNotification(err.message || 'Failed to delete search', 'error');
    } finally {
      setActionLoading(null);
      setDeleteDialogOpen(false);
      setSearchToDelete(null);
    }
  };

  const showNotification = (message: string, severity: 'success' | 'info' | 'warning' | 'error') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Saved Searches
      </Typography>
      
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      ) : searches.length === 0 ? (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body1">
            You don't have any saved searches yet.
          </Typography>
          <Typography variant="body1">
            Run a search and click "Save this search" to create alerts for new papers.
          </Typography>
        </Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }} aria-label="saved searches table">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Query</TableCell>
                <TableCell>Databases</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Last Check</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {searches.map((search) => (
                <TableRow key={search.id}>
                  <TableCell>{search.name}</TableCell>
                  <TableCell>{search.query}</TableCell>
                  <TableCell>{search.databases}</TableCell>
                  <TableCell>{search.frequency}</TableCell>
                  <TableCell>{formatDate(search.last_check_timestamp)}</TableCell>
                  <TableCell>
                    {search.active ? (
                      <Chip label="Active" color="success" size="small" />
                    ) : (
                      <Chip label="Inactive" color="default" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        variant="outlined"
                        size="small"
                        color="primary"
                        startIcon={<PlayArrowIcon />}
                        disabled={!!actionLoading}
                        onClick={() => handleRunSearch(search.id)}
                      >
                        {actionLoading === search.id ? (
                          <CircularProgress size={20} />
                        ) : (
                          'Run'
                        )}
                      </Button>
                      
                      <Button
                        variant="outlined"
                        size="small"
                        color="info"
                        startIcon={<BugReportIcon />}
                        disabled={!!actionLoading}
                        onClick={() => handleTestAlert(search.id)}
                      >
                        Test
                      </Button>
                      
                      <Button
                        variant="outlined"
                        size="small"
                        color={search.active ? 'warning' : 'success'}
                        startIcon={search.active ? <PauseIcon /> : <CheckCircleIcon />}
                        disabled={!!actionLoading}
                        onClick={() => handleToggleSearch(search.id)}
                      >
                        {search.active ? 'Pause' : 'Activate'}
                      </Button>
                      
                      <IconButton
                        color="error"
                        size="small"
                        disabled={!!actionLoading}
                        onClick={() => openDeleteDialog(search.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      
      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this saved search?
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={!!actionLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteSearch}
            disabled={!!actionLoading}
            color="error"
            variant="contained"
          >
            {actionLoading === searchToDelete ? (
              <CircularProgress size={20} />
            ) : (
              'Delete'
            )}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Notifications */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SavedSearchesPage;