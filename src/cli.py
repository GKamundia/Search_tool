import argparse
import os
from scholarly_search import ScholarSearch

def main():
    parser = argparse.ArgumentParser(description='Google Scholar Search Tool')
    parser.add_argument("--query", type=str, required=True,
                       help="Search query (supports Google Scholar syntax)")
    parser.add_argument("--scholar-max", type=int, default=50,
                       help="Maximum results from Google Scholar (default: 50)")
    parser.add_argument("--pubmed-max", type=int, default=100,
                       help="Maximum results from PubMed (default: 100)") 
    parser.add_argument("--use-fuzzy", action="store_true",
                       help="Enable fuzzy matching for deduplication")
    parser.add_argument("--fuzzy-threshold", type=int, default=85,
                       help="Similarity threshold for fuzzy matching (0-100)")

    args = parser.parse_args()
    
    try:
        # Create required directories
        if not os.path.exists('logs'):
            os.makedirs('logs')
        if not os.path.exists('data'):
            os.makedirs('data')
            
        searcher = ScholarSearch(
            scholar_max=args.scholar_max,
            pubmed_max=args.pubmed_max, 
            use_fuzzy=args.use_fuzzy,
            fuzzy_threshold=args.fuzzy_threshold
        )
        searcher.execute_search(args.query)
    except Exception as e:
        print(f"Critical error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
