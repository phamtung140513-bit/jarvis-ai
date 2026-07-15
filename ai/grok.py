"""Async OpenAI-compatible chat client (Groq / OpenRouter / xAI / Ollama)."""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Sequence

import httpx

from ai.prompts import build_system_prompt
from config import Settings, get_settings

logger = logging.getLogger(__name__)


class GrokError(RuntimeError):
    """Raised when the LLM API returns an error."""


class GrokClient:
    """Thin async wrapper around POST /chat/completions (any OpenAI-compatible API)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        # Runtime override (owner /setmodel) — does not rewrite .env
        self._model_override: str | None = None
        headers = {
            "Authorization": f"Bearer {self.settings.resolved_api_key}",
            "Content-Type": "application/json",
        }
        # OpenRouter recommends these optional headers
        if self.settings.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/TungDevAI"
            headers["X-Title"] = self.settings.app_name

        self._client = httpx.AsyncClient(
            base_url=self.settings.resolved_base_url,
            headers=headers,
            timeout=httpx.Timeout(120.0, connect=15.0),
        )
        logger.info(
            "LLM client: provider=%s model=%s url=%s",
            self.settings.provider,
            self.active_model,
            self.settings.resolved_base_url,
        )

    @property
    def active_model(self) -> str:
        return (self._model_override or self.settings.resolved_model).strip()

    def set_model_override(self, model: str | None) -> str:
        """Set runtime model id (same provider/base_url). Empty = back to .env default."""
        if model is None or not str(model).strip():
            self._model_override = None
        else:
            self._model_override = str(model).strip()
        logger.info("Model override → %s", self.active_model)
        return self.active_model

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> GrokClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def _build_payload(
        self,
        messages: Sequence[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        sys_content = build_system_prompt(system)
        full: list[dict[str, str]] = [{"role": "system", "content": sys_content}]
        full.extend(messages)
        return {
            "model": self.active_model,
            "messages": full,
            "temperature": temperature
            if temperature is not None
            else self.settings.temperature,
            "max_tokens": max_tokens
            if max_tokens is not None
            else self.settings.max_tokens,
            "stream": stream,
        }

    async def chat(
        self,
        messages: Sequence[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Send a chat completion request and return assistant text."""
        payload = self._build_payload(
            messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        logger.debug(
            "LLM request provider=%s model=%s msgs=%d",
            self.settings.provider,
            payload["model"],
            len(payload["messages"]),
        )
        try:
            resp = await self._client.post("/chat/completions", json=payload)
        except httpx.HTTPError as exc:
            logger.exception("LLM network error")
            raise GrokError(f"Network error: {exc}") from exc

        if resp.status_code >= 400:
            body = resp.text[:500]
            logger.error("LLM API %s: %s", resp.status_code, body)
            raise GrokError(f"API {resp.status_code}: {body}")

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GrokError(f"Unexpected response shape: {data!r}") from exc

        if not isinstance(content, str):
            content = str(content)
        return content.strip()

    async def chat_stream(
        self,
        messages: Sequence[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Stream assistant tokens (SSE). Yields text deltas."""
        import json

        payload = self._build_payload(
            messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        try:
            async with self._client.stream("POST", "/chat/completions", json=payload) as resp:
                if resp.status_code >= 400:
                    body = (await resp.aread()).decode(errors="replace")[:500]
                    raise GrokError(f"API {resp.status_code}: {body}")
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {}).get("content")
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                        continue
        except httpx.HTTPError as exc:
            raise GrokError(f"Network error: {exc}") from exc


# Alias for clarity in new code
LLMClient = GrokClient
LLMError = GrokError
