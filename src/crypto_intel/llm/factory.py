import structlog

from crypto_intel.llm.groq_provider import GroqProvider
from crypto_intel.llm.provider import LLMProvider
from crypto_intel.llm.template_provider import TemplateProvider

log = structlog.get_logger()


def create_provider(groq_api_key: str = "") -> LLMProvider:
    if groq_api_key:
        log.info("llm.provider.groq", model="llama-3.1-8b-instant")
        return GroqProvider(api_key=groq_api_key)

    log.info("llm.provider.template", reason="no GROQ_API_KEY set")
    return TemplateProvider()
