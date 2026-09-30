"""
Client for the File Store Bot's Link Generation API (see API_DOCS.md).

Turns Dump Channel message(s) into a monetized delivery link, automatically -
no manual "upload it there yourself and paste the link back" step needed.

How this fits together: this bot's Dump Channel is not a channel the File
Store Bot already stores in, so every request here automatically falls into
"copy" mode (per the docs) - the File Store Bot copies the message(s)
server-side the first time a link is requested. For that to work, **the
File Store Bot must be added as an admin to this bot's Dump Channel** so it
can read what it's copying. See the 🗄 File Store Bot settings screen
(/settings) for the full setup checklist and a "🔌 Test Connection" button
that calls /api/v1/ping.

Every function here fails soft: on any error (not configured, network
error, bad response, rate limited, etc.) it logs a warning and returns
None rather than raising, so a File Store Bot hiccup never blocks a post
from publishing - callers fall back to this bot's own delivery instead.
"""
import asyncio

import requests

from bot import Vars, logger

_TIMEOUT_SINGLE = 30    # seconds - one copy/url/upload
_TIMEOUT_BATCH = 120    # seconds - the docs note batch writes are one at a time
_MAX_BATCH = 100        # the API's own per-request limit


def configured() -> bool:
    return bool(Vars.FILESTORE_ENABLED and Vars.FILESTORE_API_URL and Vars.FILESTORE_API_KEY)


def _base_url() -> str:
    return Vars.FILESTORE_API_URL.rstrip("/")


def _headers() -> dict:
    return {"Authorization": f"Bearer {Vars.FILESTORE_API_KEY}"}


async def _request(method: str, path: str, timeout: int, **kw):
    """One HTTP call with a single retry on 429 (capped wait), per the docs'
    'Good habits' section. Returns the parsed JSON body, or None on any
    failure - never raises."""
    url = f"{_base_url()}{path}"
    fn = requests.post if method == "POST" else requests.get

    for attempt in range(2):
        try:
            resp = await asyncio.to_thread(fn, url, headers=_headers(), timeout=timeout, **kw)
        except requests.RequestException as e:
            logger.warning(f"File Store API request failed ({path}): {e}")
            return None

        if resp.status_code == 429 and attempt == 0:
            wait = 5
            try:
                wait = min(float(resp.headers.get("Retry-After", 5)), 10)
            except (TypeError, ValueError):
                pass
            await asyncio.sleep(wait)
            continue

        try:
            data = resp.json()
        except ValueError:
            logger.warning(f"File Store API returned non-JSON ({path}): HTTP {resp.status_code}")
            return None

        if not data.get("ok"):
            logger.warning(f"File Store API error ({path}): {data.get('error')} - {data.get('message')}")
            return None
        return data

    return None


async def ping() -> dict:
    """GET /api/v1/ping - used by the settings panel's Test Connection
    button. Deliberately only requires the URL+key to be set, not the
    FILESTORE_ENABLED toggle - so an admin can verify the connection works
    before switching it on for real posts. Returns the raw response dict
    (bot, key_label, version) on success, or None."""
    if not (Vars.FILESTORE_API_URL and Vars.FILESTORE_API_KEY):
        return None
    return await _request("GET", "/api/v1/ping", 15)


async def create_link(dump_channel_id: int, message_ids: list) -> str:
    """Turn one or more Dump Channel messages into a File Store Bot link.
    Returns the link string, or None if not configured / over the batch
    limit / the call failed for any reason - callers should fall back to
    this bot's own delivery in that case."""
    if not configured() or not dump_channel_id or not message_ids:
        return None
    if len(message_ids) > _MAX_BATCH:
        logger.warning(
            f"File Store API: {len(message_ids)} files is over the {_MAX_BATCH}-per-link "
            "limit - falling back to this bot's own delivery for this post."
        )
        return None

    if len(message_ids) == 1:
        data = await _request(
            "POST", "/api/v1/links/single", _TIMEOUT_SINGLE,
            json={"source_chat_id": dump_channel_id, "message_id": message_ids[0]},
        )
    else:
        data = await _request(
            "POST", "/api/v1/links/batch", _TIMEOUT_BATCH,
            json={"source_chat_id": dump_channel_id, "message_ids": message_ids},
        )
    return data.get("link") if data else None
