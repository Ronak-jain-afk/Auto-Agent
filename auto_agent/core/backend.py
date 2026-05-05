from abc import ABC, abstractmethod
import requests

class LLMBackend(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str,
        max_tokens: int = 512,
        temperature: float = 0.2
    ) -> str:
        """Generates a response from the LLM."""
        raise NotImplementedError

class OllamaBackend(LLMBackend):
    def __init__(self, model: str = "gemma", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(
        self,
        prompt: str,
        system: str,
        max_tokens: int = 1024,
        temperature: float = 0.2
    ) -> str:
        try:
            res = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system,        # native system field
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                },
                timeout=120
            )
            res.raise_for_status()
            data = res.json()
            if "response" not in data:
                raise ValueError(f"Unexpected Ollama response shape: {data}")
            return data["response"]
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM request failed: {e}")

class LlamaCppBackend(LLMBackend):
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def generate(
        self,
        prompt: str,
        system: str,
        max_tokens: int = 1024,
        temperature: float = 0.2
    ) -> str:
        try:
            full_prompt = f"{system}\n\n{prompt}"
            res = requests.post(
                f"{self.base_url}/completion",
                json={
                    "prompt": full_prompt,
                    "n_predict": max_tokens,
                    "temperature": temperature,
                },
                timeout=120
            )
            res.raise_for_status()
            data = res.json()
            if "content" not in data:
                raise ValueError(f"Unexpected llama.cpp response shape: {data}")
            return data["content"]
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM request failed: {e}")

class GeminiBackend(LLMBackend):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system: str, max_tokens: int = 2048, temperature: float = 0.2) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=60)
            res.raise_for_status()
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")

class OpenAIBackend(LLMBackend):
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str, system: str, max_tokens: int = 2048, temperature: float = 0.2) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=60)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"OpenAI API Error: {str(e)}")

class AnthropicBackend(LLMBackend):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20240620"):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system: str, max_tokens: int = 2048, temperature: float = 0.2) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=60)
            res.raise_for_status()
            data = res.json()
            return data["content"][0]["text"]
        except Exception as e:
            raise RuntimeError(f"Anthropic API Error: {str(e)}")

class OpenRouterBackend(OpenAIBackend):
    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        super().__init__(api_key, model, base_url="https://openrouter.ai/api/v1")

def build_backend(backend_type: str, **kwargs) -> LLMBackend:
    if backend_type == "ollama":
        return OllamaBackend(**kwargs)
    elif backend_type == "llamacpp":
        return LlamaCppBackend(**kwargs)
    elif backend_type == "gemini":
        return GeminiBackend(**kwargs)
    elif backend_type == "openai":
        return OpenAIBackend(**kwargs)
    elif backend_type == "anthropic":
        return AnthropicBackend(**kwargs)
    elif backend_type == "openrouter":
        return OpenRouterBackend(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend_type}")
