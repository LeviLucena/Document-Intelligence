from ..config import settings
from .base import Provider


def get_provider() -> Provider:
    if settings.provider == "bedrock":
        from .bedrock import BedrockProvider

        return BedrockProvider()
    from .local import LocalProvider

    return LocalProvider()
