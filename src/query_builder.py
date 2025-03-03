class QueryBuilder:
    def build_google_query(self, title=None, author=None, site=None):
        query = []
        if title:
            query.append(f'"{title}"')  # Exact phrase match
        if author:
            query.append(f'author:"{author}"')
        if site:
            query.append(f'site:{site}')
        return ' '.join(query)

    def build_pubmed_query(self, title=None, abstract=None, author=None):
        query = []
        if title:
            query.append(f'"{title}"[Title]')
        if abstract:
            query.append(f'"{abstract}"[Abstract]')
        if author:
            query.append(f'{author}[Author]')
        return ' AND '.join(query)
