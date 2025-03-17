class QueryBuilder:
    def __init__(self):
        self.terms = []
        self.filters = []
        
    def add_term(self, term: str, field: str = ""):
        if field:
            self.terms.append(f"{term}[{field}]")
        else:
            self.terms.append(term)
        return self
            
    def AND(self):
        self.terms.append("AND")
        return self
        
    def OR(self):
        self.terms.append("OR")
        return self
        
    def NOT(self):
        self.terms.append("NOT")
        return self
        
    def add_wildcard(self, term: str):
        self.terms.append(f"{term}*")
        return self
        
    def date_range(self, start_year: int, end_year: int):
        self.filters.append(f"{start_year}:{end_year}[dp]")
        return self
        
    def build(self):
        query = " ".join(self.terms)
        if self.filters:
            query += " AND " + " AND ".join(self.filters)
        return query

    def arxiv_query(self):
        """Convert PubMed-style query to arXiv syntax"""
        arxiv_terms = []
        field_map = {
            "[Title]": "ti:",
            "[Title/Abstract]": "all:",
            "[Author]": "au:",
            "[Journal]": "jr:",
        }
        
        for term in self.terms:
            if term in ("AND", "OR", "NOT"):
                arxiv_terms.append(term)
                continue
                
            # Handle field-specific terms
            for field, prefix in field_map.items():
                if field in term:
                    clean_term = term.replace(field, "")
                    arxiv_terms.append(f'{prefix}"{clean_term}"')
                    break
            else:
                # Handle wildcards and plain terms
                if "*" in term:
                    arxiv_terms.append(f'"{term}"')
                else:
                    arxiv_terms.append(term)
                    
        return " ".join(arxiv_terms)

# Example usage:
# (QueryBuilder()
#     .add_term("COVID-19", "Title/Abstract")
#     .AND()
#     .add_wildcard("vaccin*")
#     .NOT()
#     .add_term("animal")
#     .date_range(2020, 2023)
#     .build())
