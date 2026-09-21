"""
Swappable messaging providers (FIX-P11-17).

V1: WhatsApp via wa.me deep link (agent opens chat; no Cloud API).
Later: WhatsApp Cloud API / other channels behind the same port.
"""
from abc import ABC, abstractmethod
from typing import Dict
from urllib.parse import quote


class MessagingProvider(ABC):
    @property
    @abstractmethod
    def channel(self) -> str:
        """Channel id stored on Message rows (e.g. whatsapp)."""

    @abstractmethod
    def build_outbound_url(self, phone_e164: str, text: str) -> str:
        """URL the agent uses to deliver the message (or empty if server-sent)."""


class WaMeMessagingProvider(MessagingProvider):
    """Opens WhatsApp Web/App with prefilled text. No Meta Cloud API."""

    @property
    def channel(self) -> str:
        return "whatsapp"

    def build_outbound_url(self, phone_e164: str, text: str) -> str:
        digits = phone_e164.lstrip("+")
        return f"https://wa.me/{digits}?text={quote(text)}"


def get_messaging_provider(channel: str = "whatsapp") -> MessagingProvider:
    if channel == "whatsapp":
        return WaMeMessagingProvider()
    raise ValueError(f"Unsupported messaging channel: {channel}")


def preview_urls(phone_e164: str, text: str, channel: str = "whatsapp") -> Dict[str, str]:
    provider = get_messaging_provider(channel)
    return {"wa_me_url": provider.build_outbound_url(phone_e164, text)}
