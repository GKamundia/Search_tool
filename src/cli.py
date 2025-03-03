import argparse
from scholarly_search import PubMedSearch
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description='PubMed Search Tool')
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--max-results", type=int, default=50, help="Maximum results to return")
    
    args = parser.parse_args()
    
    searcher = PubMedSearch(max_results=args.max_results)
    results = searcher.search(args.query)
    
    if results:
        save_results(results)
        print(f"Saved {len(results)} results to data/results.csv")
    else:
        print("No results found")

def save_results(results):
    df = pd.DataFrame(results)
    df.to_csv('data/results.csv', index=False)

if __name__ == "__main__":
    main()
