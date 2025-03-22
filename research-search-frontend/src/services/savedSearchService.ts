import api from './api';

export interface SavedSearch {
  id: number;
  name: string;
  query: string;
  databases: string;
  frequency: string;
  last_check_timestamp: string;
  active: boolean;
  user_email?: string;
  created_at: string;
}

export interface NewPaper {
  id: number;
  title: string;
  authors: string;
  abstract: string;
  url: string;
  database: string;
  publication_date: string;
  saved_search_id: number;
  paper_id: string;
  is_new: boolean;
  is_read: boolean;
}

const savedSearchService = {
  // Get all saved searches
  getSavedSearches: async (): Promise<SavedSearch[]> => {
    const response = await api.get<SavedSearch[]>('/saved_searches');
    return response.data;
  },

  // Save a search
  saveSearch: async (searchData: {
    search_name: string;
    query: string;
    databases: string[];
    frequency: string;
    email?: string;
    max_results: number;
    start_year?: string;
    end_year?: string;
  }): Promise<SavedSearch> => {
    const formData = new FormData();
    
    formData.append('search_name', searchData.search_name);
    formData.append('query', searchData.query);
    searchData.databases.forEach(db => {
      formData.append('databases', db);
    });
    formData.append('frequency', searchData.frequency);
    
    if (searchData.email) {
      formData.append('email', searchData.email);
    }
    
    formData.append('max_results', searchData.max_results.toString());
    
    if (searchData.start_year) {
      formData.append('start_year', searchData.start_year);
    }
    
    if (searchData.end_year) {
      formData.append('end_year', searchData.end_year);
    }
    
    const response = await api.post<SavedSearch>('/save_search', formData);
    return response.data;
  },

  // Delete a saved search
  deleteSearch: async (searchId: number): Promise<void> => {
    await api.post(`/delete_search/${searchId}`);
  },

  // Toggle a saved search (active/inactive)
  toggleSearch: async (searchId: number): Promise<SavedSearch> => {
    const response = await api.post<SavedSearch>(`/toggle_search/${searchId}`);
    return response.data;
  },

  // Run a saved search now
  runSearch: async (searchId: number): Promise<{
    success: boolean;
    search_name: string;
    new_papers_count: number;
    message?: string;
    error?: string;
  }> => {
    const response = await api.post(`/run_search/${searchId}`);
    return response.data;
  },

  // Test alert for a saved search
  testAlert: async (searchId: number): Promise<{
    success: boolean;
    search_name: string;
    new_papers_count: number;
    message?: string;
    error?: string;
  }> => {
    const response = await api.post(`/test_alert/${searchId}`);
    return response.data;
  },

  // Get new papers
  getNewPapers: async (filters?: {
    search_id?: number;
    database?: string;
  }): Promise<NewPaper[]> => {
    let url = '/new_papers';
    if (filters) {
      const params = new URLSearchParams();
      if (filters.search_id) {
        params.append('search_id', filters.search_id.toString());
      }
      if (filters.database) {
        params.append('database', filters.database);
      }
      url += `?${params.toString()}`;
    }
    const response = await api.get<NewPaper[]>(url);
    return response.data;
  },

  // Mark a paper as read
  markAsRead: async (paperId: number): Promise<void> => {
    await api.post(`/mark_as_read/${paperId}`);
  }
};

export default savedSearchService;