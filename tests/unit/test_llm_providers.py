"""Unit tests for LLM provider factory and protocol conformance."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from industrial_agents.agents._llm import LLMProvider, get_llm_provider


class TestGetLlmProvider:
    def test_unknown_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider("nonexistent-llm")

    @patch.dict("os.environ", {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-test"})
    def test_anthropic_provider_instantiated(self) -> None:
        with patch("anthropic.AsyncAnthropic"):
            provider = get_llm_provider("anthropic")
            assert isinstance(provider, LLMProvider)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"})
    def test_openai_provider_instantiated(self) -> None:
        with patch("openai.AsyncOpenAI"):
            provider = get_llm_provider("openai")
            assert isinstance(provider, LLMProvider)

    def test_bedrock_provider_instantiated(self) -> None:
        with patch("boto3.client"):
            provider = get_llm_provider("bedrock")
            assert isinstance(provider, LLMProvider)

    def test_ollama_provider_instantiated(self) -> None:
        mock_client = MagicMock()
        with patch("ollama.AsyncClient", return_value=mock_client):
            provider = get_llm_provider("ollama")
            assert isinstance(provider, LLMProvider)

    @patch.dict("os.environ", {"LLM_PROVIDER": "ollama"})
    def test_env_var_provider_selection(self) -> None:
        mock_client = MagicMock()
        with patch("ollama.AsyncClient", return_value=mock_client):
            provider = get_llm_provider()
            assert isinstance(provider, LLMProvider)


class TestLLMProviderProtocol:
    """Verify the mock LLM from conftest satisfies the Protocol."""

    def test_mock_llm_has_complete_method(self, mock_llm: object) -> None:
        assert callable(getattr(mock_llm, "complete", None))

    @pytest.mark.asyncio()
    async def test_mock_llm_complete_returns_expected_shape(
        self, mock_llm: AsyncMock
    ) -> None:
        result = await mock_llm.complete([{"role": "user", "content": "hello"}])
        assert "content" in result
        assert "model" in result
        assert "usage" in result
        assert isinstance(result["content"], list)
