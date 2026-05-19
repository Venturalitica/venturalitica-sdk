"""Public surface for the SDK's LLM provider layer.

Typical usage from inside the SDK::

    from venturalitica.llm import resolve_provider

    provider = resolve_provider("alia")              # opt-in BSC ALIA 40B
    provider = resolve_provider("hypernova")         # opt-in Multiverse Hypernova 60B
    provider = resolve_provider("cloud", api_key=…)  # Mistral Magistral
    provider = resolve_provider("auto")              # ollama or cloud based on env

    chat_model = provider.create_chat_model()        # returns a LangChain BaseChatModel

For introspection (CLI / dashboard list views)::

    from venturalitica.llm import DEFAULT_CARDS
    for card in DEFAULT_CARDS:
        print(card.short_label(), card.description)
"""

from .base import LLMProvider, ModelCard, ProviderError
from .catalog import (
    ALIA_DEFAULT,
    DEFAULT_CARDS,
    HYPERNOVA_DEFAULT,
    MISTRAL_DEFAULT,
    OLLAMA_DEFAULT,
)
from .providers import (
    AliaProvider,
    HypernovaProvider,
    MistralCloudProvider,
    OllamaProvider,
)
from .registry import (
    ALIASES,
    PROVIDERS,
    list_providers,
    normalize_provider_name,
    resolve_provider,
)

__all__ = [
    # Core abstractions
    "LLMProvider",
    "ModelCard",
    "ProviderError",
    # Default catalog
    "ALIA_DEFAULT",
    "HYPERNOVA_DEFAULT",
    "MISTRAL_DEFAULT",
    "OLLAMA_DEFAULT",
    "DEFAULT_CARDS",
    # Concrete providers
    "AliaProvider",
    "HypernovaProvider",
    "MistralCloudProvider",
    "OllamaProvider",
    # Registry surface
    "PROVIDERS",
    "ALIASES",
    "resolve_provider",
    "normalize_provider_name",
    "list_providers",
]
