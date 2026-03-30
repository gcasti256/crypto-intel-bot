from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from crypto_intel.llm.factory import create_provider
from crypto_intel.llm.groq_provider import GroqProvider
from crypto_intel.llm.provider import LLMProvider
from crypto_intel.llm.template_provider import TemplateProvider


class TestTemplateProvider:
    @pytest.mark.asyncio
    async def test_returns_prompt(self):
        provider = TemplateProvider()
        result = await provider.generate("Hello world", system="test")
        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_implements_protocol(self):
        provider = TemplateProvider()
        assert isinstance(provider, LLMProvider)


class TestGroqProvider:
    @pytest.mark.asyncio
    async def test_generate_with_mock(self):
        provider = GroqProvider(api_key="test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI response"

        provider.client = AsyncMock()
        provider.client.chat = MagicMock()
        provider.client.chat.completions = MagicMock()
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await provider.generate("Test prompt", system="Be helpful")
        assert result == "AI response"

    def test_implements_protocol(self):
        provider = GroqProvider(api_key="test")
        assert isinstance(provider, LLMProvider)


class TestFactory:
    def test_creates_groq_with_key(self):
        provider = create_provider(groq_api_key="test-key")
        assert isinstance(provider, GroqProvider)

    def test_creates_template_without_key(self):
        provider = create_provider(groq_api_key="")
        assert isinstance(provider, TemplateProvider)

    def test_creates_template_with_empty_key(self):
        provider = create_provider()
        assert isinstance(provider, TemplateProvider)
