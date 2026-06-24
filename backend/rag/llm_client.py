"""
rag/llm_client.py
LLM inference client — supports two interchangeable providers:

  1. Gemini (default)  — Google Gemini API, self-hosted Qwen 3. Used for Docker/bare-metal
     deployments where you control the infrastructure and want full data
     privacy. Requires `ollama serve` running and a model pulled.

  2. Groq               — free hosted inference, OpenAI-compatible API.
     Used for free-tier demo deployments (e.g. Render free tier, which has
     no GPU and not enough RAM/disk to run Ollama). Get a free key at
     https://console.groq.com/keys — no credit card required.

Switch providers with the LLM_PROVIDER environment variable:
    LLM_PROVIDER=gemini   (default)
    LLM_PROVIDER=groq

The public interface (chat, chat_stream, generate, is_available) is
identical regardless of provider, so nothing else in the codebase needs to
change when you switch.
"""

import json
import logging
import os
from typing import Generator, Optional

import requests

logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

# ── Ollama config ────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_TIMEOUT  = int(os.getenv("OLLAMA_TIMEOUT", 120))

# ── Groq config ──────────────────────────────────────────────
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TIMEOUT  = int(os.getenv("GROQ_TIMEOUT", 60))

# ── Gemini config ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


class LLMClient:
    """
    Provider-agnostic LLM client. Picks Gemini, Ollama, or Groq based on
    LLM_PROVIDER, but exposes the same chat()/chat_stream()/generate()
    interface either way.
    """

    def __init__(self, provider: str = None, base_url: str = None,
                 model: str = None, timeout: int = None, api_key: str = None):
        self.provider = (provider or LLM_PROVIDER).lower()

        if self.provider == "groq":
            self.base_url = base_url or GROQ_BASE_URL
            self.model = model or GROQ_MODEL
            self.timeout = timeout or GROQ_TIMEOUT
            self.api_key = api_key or GROQ_API_KEY
        elif self.provider == "gemini":
            self.base_url = base_url
            self.model = model or GEMINI_MODEL
            self.timeout = timeout or 60
            self.api_key = api_key or GEMINI_API_KEY
        else:
            self.provider = "ollama"
            self.base_url = base_url or OLLAMA_BASE_URL
            self.model = model or OLLAMA_MODEL
            self.timeout = timeout or OLLAMA_TIMEOUT
            self.api_key = None

    # ── Health ──────────────────────────────────────────────
    def is_available(self) -> bool:
        try:
            if self.provider == "gemini":
                return bool(self.api_key)
            if self.provider == "groq":
                if not self.api_key:
                    return False
                resp = requests.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                    timeout=5,
                )
                return resp.ok
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.ok
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            if self.provider == "gemini":
                return [self.model, "gemini-1.5-flash", "gemini-2.0-flash"]
            if self.provider == "groq":
                resp = requests.get(f"{self.base_url}/models", headers=self._headers(), timeout=5)
                if resp.ok:
                    return [m["id"] for m in resp.json().get("data", [])]
                return []
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.ok:
                return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
        return []

    def _headers(self) -> dict:
        if self.provider == "groq":
            return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        return {"Content-Type": "application/json"}

    # ── Chat completion ─────────────────────────────────────
    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        system: Optional[str] = None,
    ) -> str:
        """
        Non-streaming chat completion.

        Args:
            messages: [{ "role": "user"|"assistant"|"system", "content": "..." }]
            temperature: sampling temperature (0 = deterministic)
            max_tokens: max tokens to generate
            system: optional system prompt prepended

        Returns:
            The model's response text.
        """
        if self.provider == "gemini":
            from services.gemini_service import gemini_service
            # Create a localized service to use the correct model/api_key if overridden
            svc = gemini_service
            if self.api_key != GEMINI_API_KEY or self.model != GEMINI_MODEL:
                from services.gemini_service import GeminiService
                svc = GeminiService(api_key=self.api_key, model=self.model)
            return svc.chat(messages, system_instruction=system)

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        if self.provider == "groq":
            return self._chat_groq(full_messages, temperature, max_tokens)
        return self._chat_ollama(full_messages, temperature, max_tokens)

    def _chat_ollama(self, full_messages: list[dict], temperature: float, max_tokens: int) -> str:
        payload = {
            "model": self.model,
            "messages": full_messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "").strip()
        except requests.exceptions.ConnectionError as exc:
            logger.error("Ollama connection failed: %s", exc)
            raise RuntimeError(
                "Cannot connect to Ollama. Ensure 'ollama serve' is running "
                f"and the model '{self.model}' is pulled (ollama pull {self.model})."
            ) from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Ollama request timed out: %s", exc)
            raise RuntimeError("LLM request timed out. Try a shorter query.") from exc
        except Exception as exc:
            logger.error("Ollama chat failed: %s", exc)
            raise RuntimeError(f"LLM inference failed: {exc}") from exc

    def _chat_groq(self, full_messages: list[dict], temperature: float, max_tokens: int) -> str:
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys "
                "and set it in your environment variables."
            )
        payload = {
            "model": self.model,
            "messages": full_messages,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload, headers=self._headers(), timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except requests.exceptions.ConnectionError as exc:
            logger.error("Groq connection failed: %s", exc)
            raise RuntimeError("Cannot connect to Groq API. Check your internet connection.") from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Groq request timed out: %s", exc)
            raise RuntimeError("LLM request timed out. Try a shorter query.") from exc
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            if status == 401:
                raise RuntimeError("Groq API key is invalid. Check GROQ_API_KEY.") from exc
            if status == 429:
                raise RuntimeError("Groq free-tier rate limit hit. Wait a moment and try again.") from exc
            logger.error("Groq chat failed: %s", exc)
            raise RuntimeError(f"LLM inference failed: {exc}") from exc
        except Exception as exc:
            logger.error("Groq chat failed: %s", exc)
            raise RuntimeError(f"LLM inference failed: {exc}") from exc

    # ── Streaming chat completion ───────────────────────────
    def chat_stream(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        system: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Streaming chat completion — yields text chunks as they arrive."""
        if self.provider == "gemini":
            yield self.chat(messages, temperature, max_tokens, system)
            return

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        if self.provider == "groq":
            yield from self._chat_stream_groq(full_messages, temperature, max_tokens)
        else:
            yield from self._chat_stream_ollama(full_messages, temperature, max_tokens)

    def _chat_stream_ollama(self, full_messages, temperature, max_tokens):
        payload = {
            "model": self.model,
            "messages": full_messages,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            with requests.post(f"{self.base_url}/api/chat", json=payload, stream=True, timeout=self.timeout) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break
        except Exception as exc:
            logger.error("Ollama streaming failed: %s", exc)
            yield f"\n\n[Error: {exc}]"

    def _chat_stream_groq(self, full_messages, temperature, max_tokens):
        if not self.api_key:
            yield "\n\n[Error: GROQ_API_KEY is not set]"
            return
        payload = {
            "model": self.model, "messages": full_messages, "stream": True,
            "temperature": temperature, "max_tokens": max_tokens,
        }
        try:
            with requests.post(
                f"{self.base_url}/chat/completions", json=payload,
                headers=self._headers(), stream=True, timeout=self.timeout,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line or line == b"data: [DONE]":
                        continue
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        decoded = decoded[6:]
                    try:
                        chunk = json.loads(decoded)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        except Exception as exc:
            logger.error("Groq streaming failed: %s", exc)
            yield f"\n\n[Error: {exc}]"

    # ── Simple generate (no chat history) ───────────────────
    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
        """Simple completion without chat formatting — useful for structured extraction."""
        return self.chat(messages=[{"role": "user", "content": prompt}], temperature=temperature, max_tokens=max_tokens)


# Singleton instance for convenience imports — provider chosen via LLM_PROVIDER env var
llm_client = LLMClient()
