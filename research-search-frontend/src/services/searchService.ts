// src/services/searchService.ts
import api from './api';

export interface SearchParams {
  terms: string[];
  operators: string[];
  fields: string[];
  databases: string[];
  startYear?: string;
  endYear?: string;
  maxResults: number;
}

export interface SearchResults {
  pubmed: any[];
  arxiv: any[];
  gim: any[];
}

const searchService = {
  performSearch: async (params: SearchParams): Promise<SearchResults> => {
    const formData = new FormData();
    
    // Add all parameters to form data
    params.terms.forEach((term, i) => {
      formData.append('term', term);
      if (params.operators[i]) formData.append('boolean_operator', params.operators[i]);
      if (params.fields[i]) formData.append('field', params.fields[i]);
    });
    
    params.databases.forEach(db => {
      formData.append('databases', db);
    });
    
    if (params.startYear) formData.append('start_year', params.startYear);
    if (params.endYear) formData.append('end_year', params.endYear);
    formData.append('max_results', params.maxResults.toString());
    
    const response = await api.post('/search', formData);
    return response.data;
  }
};

export default searchService;