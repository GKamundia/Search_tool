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

interface SearchResponse {
  query: string;
  results: SearchResults;
}

// Map frontend field values to backend field values
const mapFieldToBackend = (field: string): string => {
  const fieldMap: {[key: string]: string} = {
    'title': '[Title]',
    'title_abstract': '[Title/Abstract]',
    'abstract': '[Abstract]',
    'author': '[Author]',
    'journal': '[Journal]',
    'keyword': '[Keyword]',
    'mesh': '[MeSH Terms]'
  };
  
  return fieldMap[field] || '';
};

const searchService = {
  performSearch: async (params: SearchParams): Promise<SearchResponse> => {
    const formData = new FormData();
    
    // Add all parameters to form data
    params.terms.forEach((term, i) => {
      formData.append('term', term);
      if (params.operators[i]) formData.append('boolean_operator', params.operators[i]);
      // Map field values to match backend expectations
      if (params.fields[i]) {
        const mappedField = mapFieldToBackend(params.fields[i]);
        formData.append('field', mappedField);
      } else {
        formData.append('field', '');
      }
    });
    
    params.databases.forEach(db => {
      formData.append('databases', db);
    });
    
    if (params.startYear) formData.append('start_year', params.startYear);
    if (params.endYear) formData.append('end_year', params.endYear);
    formData.append('max_results', params.maxResults.toString());
    
    try {
      const response = await api.post<SearchResponse>('/search', formData);
      return response.data;
    } catch (error: any) {
      console.error('Search API error:', error);
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      }
      throw error;
    }
  }
};

export default searchService;