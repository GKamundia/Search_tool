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


# Example usage:
# (QueryBuilder()
#     .add_term("COVID-19", "Title/Abstract")
#     .AND()
#     .add_wildcard("vaccin*")
#     .NOT()
#     .add_term("animal")
#     .date_range(2020, 2023)
#     .build())
