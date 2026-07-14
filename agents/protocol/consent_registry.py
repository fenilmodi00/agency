"""Consent Registry agent — canonical consent and live-suppression authority.

SAFETY-CRITICAL: Emphasizes deny-only suppression path and data-subject
erasure authority. Read-only utility agent — does NOT export get_*_task().
"""

from pathlib import Path

from agents._base import Agent, load_prompt

from config import MODEL_PROTOCOL_REGISTRY
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get, registry_propose, registry_verify

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def get_consent_registry_agent() -> Agent:
    """Return a CrewAI Agent for consent/suppression registry operations.

    SAFETY-CRITICAL: This agent handles opt-in evidence, immediate
    suppress events (deny-only — any validated producer may suppress),
    data-subject erasure, and restore operations. Suppress is deliberately
    deny-only: a bad producer can cause non-contact but cannot erase,
    restore, or authorize a send.
    """
    prompt = load_prompt(_PROMPTS_DIR, "consent_registry_prompt.txt")

    return Agent(
        role=prompt.get("Role") or "Consent Registry — Canonical Consent and Live-Suppression Authority",
        goal=prompt.get("Goal") or (
            "Manage consent and live-suppression records: query suppression "
            "state, submit propose events for opt-in evidence, and enforce "
            "deny-only immediate suppress for unsubscribes/complaints/bounces."
        ),
        backstory=prompt.get("Backstory") or (
            "I am the consent-registry principal operating under host-capability "
            "authority. I record opt-in/lawful-basis evidence, immediately "
            "suppress on unsubscribe/hard-bounce/complaint, process data-subject "
            "erasure requests, and support restore after fresh authorized opt-in. "
            "The suppress path is deliberately deny-only: any validated producer "
            "may suppress immediately because it cannot authorize contact or "
            "clear state. Erasure and restore require host-capability authority. "
            "I never store email, phone, name, or address in aggregate IDs, "
            "payloads, or reports — only pseudonymous subject IDs and minimum "
            "proof pointers."
        ),
        llm=get_fireworks_llm(MODEL_PROTOCOL_REGISTRY),
        tools=[registry_get, registry_propose, registry_verify],
        verbose=True,
        allow_delegation=False,
    )
