"""Test script: send a demo paid-collab DM to @fenil_modii.

Handles Chrome cookie -> instagrapi session conversion, LLM-based DM drafting,
and actual DM sending via the send_instagram_dm tool.

Usage:
    python test_dm.py          # dry-run (draft only, no send)
    python test_dm.py --send   # actually send the DM
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    FIREWORKS_API_KEY,
    FIREWORKS_BASE_URL,
    IG_PASSWORD,
    IG_SESSION_FILE,
    IG_USERNAME,
    LOG_LEVEL,
    MODEL_ACTIVATE_OUTREACH,
)

logger.remove()
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
)


def convert_chrome_cookies(chrome_path: str, settings_path: str) -> bool:
    """Convert Chrome cookie JSON to instagrapi settings JSON.

    Chrome exports: [{"domain":".instagram.com","name":"sessionid","value":"xxx"},...]
    instagrapi expects: {"cookies": {"sessionid": "xxx", "ds_user_id": "yyy"}}

    Returns True if conversion succeeded.
    """
    with open(chrome_path, encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, dict) and "cookies" in raw:
        logger.info("File already in instagrapi settings format — using as-is")
        return True

    cookies: dict[str, str] = {}
    for entry in raw if isinstance(raw, list) else []:
        if not isinstance(entry, dict):
            continue
        if "instagram.com" in entry.get("domain", ""):
            cookies[entry["name"]] = entry["value"]

    if not cookies:
        logger.error("No Instagram cookies found in {}", chrome_path)
        return False

    settings = {"cookies": cookies}
    os.makedirs(os.path.dirname(settings_path) or ".", exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    logger.info("Converted {} Chrome cookies -> instagrapi settings at {}", len(cookies), settings_path)
    return True


def _is_analysis_paragraph(text: str) -> bool:
    return text.startswith(("*", "-", "1.", "2.", "3.", "###"))


def _find_vernacular_text(text: str) -> str | None:
    import re

    vernacular_range = r"[\u0900-\u097F\u0A80-\u0AFF\u1CD0-\u1CFF\uA8E0-\uA8FF]"
    match = re.search(rf"({vernacular_range}{{50,}})", text)
    return match.group(1).strip() if match else None


THINKING_MARKERS = [
    "Thinking Process:",
    "**Analyze the Request:**",
    "1.  **Analyze the Request:**",
    "Let me count characters",
    "Let me check",
    "Let me verify",
]


def _extract_dm_text(raw: str) -> str:
    import re

    quoted = re.findall(r'"([^"]{30,})"', raw)
    if quoted:
        return quoted[-1].strip()

    for marker in THINKING_MARKERS:
        idx = raw.find(marker)
        if idx >= 0:
            vernacular = _find_vernacular_text(raw[idx + len(marker) :])
            if vernacular:
                return vernacular
            break

    lines = raw.split("\n")
    dm_lines = [
        l.strip() for l in lines
        if l.strip()
        and not _is_analysis_paragraph(l)
        and "Count:" not in l
        and "Attempt" not in l
        and len(l.strip()) > 20
    ]
    if dm_lines:
        return dm_lines[-1]

    return raw.strip()


DM_CONTEXT = (
    "Brand: Ambika Fast Food Shop. Campaign: Buy One Get One (BOGO) pizza promotion. "
    "Creator has ~2000 followers, ~20K avg views. Our offered rate: 800 INR. "
    "Ask what their expected rate is for this collab."
)

DM_FALLBACK = (
    "Hey Fenil! We're from Ambika Fast Food Shop — we're launching a Buy One Get One "
    "pizza offer and your content style would be perfect for promoting it. This is a "
    "paid collaboration, and we're offering around 800 INR for it. What's your expected "
    "rate? Let us know if you're interested, would love to work together!"
)


def _try_draft_with_model(username: str, model: str, context: str = "") -> str | None:
    from openai import OpenAI

    llm = OpenAI(api_key=FIREWORKS_API_KEY, base_url=FIREWORKS_BASE_URL)

    system_prompt = (
        "You write short, warm Instagram DMs in English for paid brand collaborations. "
        "Output ONLY the DM text. No analysis, no markdown, no quotes."
    )

    base_prompt = (
        f"DM to @{username}: propose paid collab in English. "
        "Mention 'paid collaboration' and include all brand/offer details provided. "
        "Ask what their expected rate is. Mention our offered rate. "
        "Appreciate content style. Ask if interested. 200-350 chars. ONE paragraph."
    )

    user_prompt = f"{base_prompt}\n\nBrand details: {context}" if context else base_prompt

    response = llm.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=800,
        temperature=0.85,
    )

    content = response.choices[0].message.content
    if content is None:
        return None
    raw = content.strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1].strip()

    raw = _extract_dm_text(raw)

    if len(raw) < 30:
        return None
    thinking_starts = (
        "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.",
        "**", "Let me", "I'll", "Here", "The ", "Okay", "Sure",
        "Of course", "Characters:", "Character", "Count:",
        "*   *", "* *", "(",
    )
    if raw.startswith(thinking_starts):
        return None
    if any(marker in raw for marker in [
        "**Analyze", "**Drafting", "**Formatting Check",
        "Let's do exact", "chars including", "total 13 chars",
    ]):
        return None

    return raw


def draft_paid_collab_dm(username: str, context: str = "") -> str:
    from openai import OpenAI

    if not context:
        return DM_FALLBACK

    for model in [
        "accounts/fireworks/models/deepseek-v4-flash",
        "accounts/fireworks/models/deepseek-v4-pro",
    ]:
        logger.info("Trying model: {}", model)
        try:
            result = _try_draft_with_model(username, model, context)
        except Exception as exc:
            logger.warning("Model {} failed: {}", model, exc)
            continue
        if result and len(result) > 50:
            logger.info("Model {} produced clean DM ({} chars)", model, len(result))
            return result
        logger.warning("Model {} output rejected ({} chars), trying next...", model, len(result) if result else 0)

    logger.info("All LLM models failed — using fallback DM")
    return DM_FALLBACK


def _resolve_user_id(client, username: str) -> int | None:
    """Try multiple endpoints to resolve username->user_id, avoiding 429 limits."""
    strategies = [
        ("user_id_from_username", lambda: client.user_id_from_username(username)),
        ("user_info_by_username", lambda: _resolve_via_user_info(client, username)),
        ("search_users", lambda: _resolve_via_search(client, username)),
    ]

    for name, strategy in strategies:
        logger.info("Resolving @{} via {}", username, name)
        try:
            uid = strategy()
            if uid:
                logger.success("@{} -> user_id={} (via {})", username, uid, name)
                return uid
        except Exception as exc:
            logger.warning("{} failed: {}", name, exc)

    return None


def _resolve_via_user_info(client, username: str) -> int | None:
    info = client.cl.user_info_by_username(username)
    return int(info.pk) if info else None


def _resolve_via_search(client, username: str) -> int | None:
    results = client.cl.search_users(username)
    for user in (results or []):
        if getattr(user, "username", "") == username:
            return int(user.pk)
    return None


def main(send: bool = False) -> dict:
    creator_username = "fenil_modii"
    converted_settings = "data/ig_settings.json"

    logger.info("=" * 50)
    logger.info("Demo DM Test — @{}", creator_username)
    logger.info("Send mode: {}", "LIVE" if send else "DRY-RUN")
    logger.info("=" * 50)

    # ── Step 1: Init Instagram client ──────────────────────────────────────
    from ig_client import get_ig_client, InstagramClient

    client = get_ig_client()
    logged_in = False

    if IG_USERNAME and IG_PASSWORD:
        logger.info("Attempting fresh login as @{}", IG_USERNAME)
        try:
            client.cl.login(IG_USERNAME, IG_PASSWORD)
            client.cl.dump_settings(converted_settings)
            client._logged_in = True
            logged_in = True
            logger.success("Fresh login succeeded as @{}", IG_USERNAME)
        except Exception as exc:
            error_msg = str(exc)
            if "429" in error_msg or "rate" in error_msg.lower():
                logger.warning("Login 429 — trying Chrome cookies as fallback")
            else:
                logger.warning("Login failed: {} — trying cookies", exc)

    if not logged_in and Path(IG_SESSION_FILE).exists():
        logger.info("Loading Chrome cookies from {}", IG_SESSION_FILE)
        if convert_chrome_cookies(IG_SESSION_FILE, converted_settings):
            try:
                client.cl.load_settings(converted_settings)
                client._logged_in = True
                client.cl.init()
                logged_in = True
                logger.success("Session loaded from converted cookies (read-only — DMs may need full auth)")
            except Exception as exc:
                logger.warning("Cookie load_settings failed: {}", exc)

    if not logged_in:
        return {"success": False, "error": "Could not establish Instagram session"}

    if send:
        _resolve_user_id(client, creator_username)

    # ── Step 3: Draft the DM ───────────────────────────────────────────────
    logger.info("Drafting paid-collaboration DM for @{}...", creator_username)

    try:
        message = draft_paid_collab_dm(creator_username, DM_CONTEXT)
    except Exception as exc:
        logger.error("LLM call failed: {}", exc)
        return {"success": False, "error": f"LLM error: {exc}"}

    logger.info("-" * 40)
    logger.info("DRAFTED DM ({} chars):", len(message))
    logger.info("{}", message)
    logger.info("-" * 40)

    # ── Step 4: Send (or skip in dry-run) ──────────────────────────────────
    if not send:
        logger.info("DRY-RUN: DM NOT sent. Re-run with --send to dispatch.")
        return {
            "success": True,
            "sent": False,
            "dry_run": True,
            "username": creator_username,
            "message": message,
            "message_length": len(message),
        }

    logger.info("Sending DM to @{}...", creator_username)

    user_id = _resolve_user_id(client, creator_username)
    if user_id is None:
        return {
            "success": False, "thread_id": None,
            "error": "Cannot resolve user_id: all endpoints returning 429 (Instagram rate-limited this IP. Try VPN/proxy or wait 15-60 min).",
            "username": creator_username,
        }

    dm_result = client.send_dm(user_id, message)

    if dm_result.get("success"):
        logger.success("DM SENT! thread_id: {}", dm_result.get("thread_id"))
    else:
        logger.error("DM FAILED: {}", dm_result.get("error"))

    return {
        **dm_result,
        "username": creator_username,
        "message": message,
        "message_length": len(message),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send demo paid-collab DM to @fenil_modii")
    parser.add_argument(
        "--send",
        action="store_true",
        default=False,
        help="Actually send the DM (default: dry-run — draft only)",
    )
    args = parser.parse_args()

    result = main(send=args.send)

    print()
    print(json.dumps(result, indent=2, ensure_ascii=True, default=str))

    if result.get("success") and not result.get("sent"):
        print("\n[OK] DM drafted successfully. Run with --send to dispatch.")
    elif result.get("success") and result.get("sent"):
        print(f"\n[OK] DM sent! thread_id: {result.get('thread_id')}")
    else:
        print(f"\n[FAIL] {result.get('error')}")
        sys.exit(1)
