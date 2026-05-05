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

def build_backend(backend_type: str, **kwargs) -> LLMBackend:
    if backend_type == "ollama":
        return OllamaBackend(**kwargs)
    elif backend_type == "llamacpp":
        return LlamaCppBackend(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend_type}")
