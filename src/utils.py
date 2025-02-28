from typing import Optional
import re
from thefuzz import fuzz

DOI_REGEX = r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$'

def validate_doi(doi: str) -> bool:
    return re.fullmatch(DOI_REGEX, doi, re.IGNORECASE) is not None

def fuzzy_match(text1: str, text2: str, threshold: int = 85) -> bool:
    return fuzz.ratio(text1.lower(), text2.lower()) >= threshold
