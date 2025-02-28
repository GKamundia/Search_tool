import argparse
from typing import Optional
from scholarly_search import ScholarSearch

def main():
    parser = argparse.ArgumentParser(description='Google Scholar Search Tool')
    parser.add_argument("--query", type=str, required=True,
                       help="Search query (supports Google Scholar syntax)")
    parser.add_argument("--max-results", type=int, default=50,
                       help="Maximum results to return")
    parser.add_argument("--use-fuzzy", action="store_true",
                       help="Enable fuzzy matching for deduplication")
    parser.add_argument("--fuzzy-threshold", type=int, default=85,
                       help="Similarity threshold for fuzzy matching (0-100)")

    args = parser.parse_args()
    
    searcher = ScholarSearch(
        max_results=args.max_results,
        use_fuzzy=args.use_fuzzy,
        fuzzy_threshold=args.fuzzy_threshold
    )
    searcher.execute_search(args.query)

if __name__ == "__main__":
    main()
