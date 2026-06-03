"""
LLM Client — built-in LLM integration for agent-driven math.

Supports any OpenAI-compatible API endpoint: Claude (Anthropic), GPT (OpenAI),
DeepSeek, or self-hosted models.

Setup:
    export MATH_AGENT_API_KEY="sk-your-key"
    export MATH_AGENT_BASE_URL="https://api.deepseek.com/anthropic"  # default
    export MATH_AGENT_MODEL="deepseek-v4-pro"                        # default

Usage:
    client = LLMClient()
    response = client.chat(system_prompt, user_message)
    response = client.chat_with_tools(system_prompt, user_message, tools)
"""

import os, json, sys
from typing import Any, Dict, List, Optional, Callable


class LLMClient:
    """OpenAI-compatible LLM client. Works with Claude, GPT, DeepSeek, etc."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("MATH_AGENT_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("MATH_AGENT_BASE_URL") or os.environ.get("ANTHROPIC_BASE_URL") or "https://api.deepseek.com/anthropic"
        self.model = model or os.environ.get("MATH_AGENT_MODEL") or os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL") or "deepseek-v4-pro"

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "anthropic-version": "2023-06-01",
        }

    def chat(self, system_prompt: str, user_message: str, temperature: float = 0.1) -> str:
        """Send a chat message and return the text response."""
        if not self.api_key:
            return self._no_key_response(system_prompt, user_message)

        import urllib.request
        import urllib.error

        # Detect if using Anthropic endpoint (messages API) or OpenAI-compatible (chat completions)
        if "anthropic" in self.base_url.lower() or "claude" in self.model.lower():
            return self._chat_anthropic(system_prompt, user_message, temperature)
        else:
            return self._chat_openai(system_prompt, user_message, temperature)

    def _chat_anthropic(self, system_prompt: str, user_message: str, temperature: float) -> str:
        import urllib.request, urllib.error
        body = json.dumps({
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }).encode("utf-8")

        url = f"{self.base_url.rstrip('/')}/v1/messages"
        req = urllib.request.Request(url, data=body, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            # Anthropic format: content[0].text
            content = data.get("content", [])
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", str(content))
            return str(content)
        except urllib.error.HTTPError as e:
            return f"[LLM Error {e.code}]: {e.reason}. Set MATH_AGENT_API_KEY to your API key."

    def _chat_openai(self, system_prompt: str, user_message: str, temperature: float) -> str:
        import urllib.request, urllib.error
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        body = json.dumps({
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": messages,
        }).encode("utf-8")

        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            return data.get("choices", [{}])[0].get("message", {}).get("content", str(data))
        except urllib.error.HTTPError as e:
            return f"[LLM Error {e.code}]: {e.reason}. Set MATH_AGENT_API_KEY to your API key."

    def _no_key_response(self, system_prompt: str, user_message: str) -> str:
        return (
            "I notice you haven't set an API key. I'll operate in local-only mode.\n\n"
            "To enable LLM-driven reasoning, set your API key:\n"
            "  export MATH_AGENT_API_KEY='sk-your-key-here'\n"
            "  export MATH_AGENT_BASE_URL='https://api.deepseek.com/anthropic'  # optional\n"
            "  export MATH_AGENT_MODEL='deepseek-v4-pro'  # optional\n\n"
            "Without an API key, I can still run defined model pipelines "
            "(math-agent derive), but cannot do free-form reasoning."
        )

    def is_available(self) -> bool:
        return bool(self.api_key)


_global_client: Optional[LLMClient] = None


def get_client() -> LLMClient:
    global _global_client
    if _global_client is None:
        _global_client = LLMClient()
    return _global_client
