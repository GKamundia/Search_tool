import os
import json
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict

class DeepSeekAdvisor:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_queries(self, user_input: str) -> Dict:
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{
                    "role": "user",
                    "content": f"""Convert this natural language request into structured PubMed and Global Index Medicus search queries:
                    
                    Request: {user_input}
                    
                    Requirements:
                    - PubMed: Use [field] syntax (e.g., [Title/Abstract])
                    - GIM: Use prefix syntax (ti:, ab:, dp:)
                    - Include boolean operators
                    - Return JSON with keys "pubmed_query" and "gim_query"
                    """
                }],
                "response_format": {"type": "json_object"}
            }
        )
        response.raise_for_status()
        return json.loads(response.json()["choices"][0]["message"]["content"])
