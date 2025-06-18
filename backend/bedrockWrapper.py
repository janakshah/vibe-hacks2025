import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class LiteLLMClient:
    """
    Robust client for interacting with the LiteLLM API, with timeout and retries.
    """
    def __init__(self, api_key: str, base_url: str = "https://litellm.rillavoice.com", 
                 timeout: float = 30.0, max_retries: int = 3, backoff_factor: float = 1.0):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = timeout
        
        # Set up a session with retry logic
        self.session = requests.Session()
        retries = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def chat_completion(self, model: str, messages: list) -> dict:
        """
        Sends a chat completion request with timeout and retries.

        Args:
            model (str): Name of the model to call.
            messages (list): List of message dicts in OpenAI chat format.

        Returns:
            dict: Parsed JSON response from the API.

        Raises:
            Exception: On timeout or HTTP error.
        """
        endpoint = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages
        }
        try:
            response = self.session.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            raise Exception(f"Request timed out after {self.timeout} seconds") from e
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}") from e

# client = LiteLLMClient(api_key="sk-rilla-vibes")
# user_input = "I own a samll chinese restaurant and I want to create marketing message to attaract more customrs, todays special is sweet and sour pork, please write a message to attract more customers, also todays date is june 17th 2025 and my restaurant is in queens, new york, use todays date and my lcoality to create some creative marketing message, I want only marketing message in output nothing else"
# messages = [{"role": "user", "content": user_input}]
# result = client.chat_completion("llama-4-maverick-17b-instruct", messages)
# print(result["choices"][0]["message"]["content"])