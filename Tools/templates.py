"""Post templates: stylish unicode fonts + optional premium (custom) emoji.

Three ready-made designs, selectable / previewable from /settings -> Post Design.
Premium emoji: each slot below can be mapped to a custom-emoji id from the bot
(/settings -> Post Design -> Premium Emoji). Unmapped slots use the plain emoji,
so posts always render, even without Telegram Premium features.
"""
import html
import re

from bot import Vars
from Tools.config import emoji_map
from Tools.fonts import stylize

# slot -> (label shown in settings, fallback emoji)
SLOTS = {
  "fire": ("Fire", "🔥"),
  "crown": ("Crown", "👑"),
  "star": ("Star", "⭐"),
  "sparkle": ("Sparkle", "✨"),
  "heart": ("Heart", "💖"),
  "genre": ("Genre", "🏷"),
  "status": ("Status", "📡"),
  "chapters": ("Chapters", "📚"),
  "format": ("Format", "📁"),
  "synopsis": ("Synopsis", "📖"),
  "arrow": ("Arrow", "👇"),
  "source": ("Source", "🌐"),
}
SLOT_ORDER = list(SLOTS)


def _emoji_tag():
  """pyrogram forks differ: <emoji id=".."> (pyrofork) vs <tg-emoji emoji-id=".."> (kurigram)."""
  try:
    import inspect
    import pyrogram.parser.html as parser
    if "tg-emoji" in inspect.getsource(parser):
      return "tg-emoji", "emoji-id"
  except Exception:
    pass
  return "emoji", "id"


_TAG, _ATTR = _emoji_tag()
_TAG_RE = re.compile(r"<[^>]+>")
_UTF16 = "utf-16-le"


def visible_len(text: str) -> int:
  return len(html.unescape(_TAG_RE.sub("", text)).encode(_UTF16)) // 2


def _tags(genres):
  out = []
  for g in genres:
    g = re.sub(r"\W+", "_", g.strip()).strip("_")
    if g:
      out.append("#" + g)
  return " ".join(out[:8])


def _split_genres(raw):
  if isinstance(raw, (list, tuple)):
    return [str(g) for g in raw]
  raw = str(raw or "")
  raw = raw.replace("#", " ")
  parts = raw.split(",") if "," in raw else raw.split()
  return [p for p in (x.strip() for x in parts) if p and p.upper() != "N/A"]


class _Ctx:
  """Formatting helpers bound to the current settings."""

  def __init__(self, premium=None, stylish=None, footer=None):
    self.stylish = Vars.POST_STYLISH if stylish is None else stylish
    self.premium = Vars.POST_PREMIUM_EMOJI if premium is None else premium
    self.footer = Vars.POST_FOOTER if footer is None else footer
    self._map = emoji_map() if self.premium else {}

  def e(self, slot):
    fallback = SLOTS[slot][1]
    cid = self._map.get(slot)
    if cid:
      return f'<{_TAG} {_ATTR}="{int(cid)}">{fallback}</{_TAG}>'
    return fallback

  def s(self, text, font):
    text = html.escape(str(text))
    return stylize(text, font) if self.stylish else text

  def label(self, text, font="smallcaps"):
    return f"<b>{self.s(text, font)}</b>"


# --------------------------------------------------------------------------- #
# templates - each returns HTML. `desc` is already escaped and length-limited.
# --------------------------------------------------------------------------- #
def t_elegant(c: _Ctx, d, desc):
  out = [f"<blockquote>{c.e('fire')} <b>{c.s(d['title'], 'bolditalic')}</b></blockquote>", ""]
  out.append(f"{c.e('genre')} {c.label('Genre')} ➜ {_tags(d['genres']) or 'N/A'}")
  out.append(f"{c.e('status')} {c.label('Status')} ➜ {html.escape(d['status'] or 'N/A')}")
  if d.get("chapters"):
    out.append(f"{c.e('chapters')} {c.label('Chapters')} ➜ {d['chapters']}")
  if d.get("formats"):
    out.append(f"{c.e('format')} {c.label('Format')} ➜ {html.escape(d['formats'])}")
  if d.get("source"):
    out.append(f"{c.e('source')} {c.label('Source')} ➜ {html.escape(d['source'])}")
  if desc:
    out += ["", f"{c.e('synopsis')} {c.label('Synopsis')}", f"<blockquote expandable>{desc}</blockquote>"]
  if c.footer:
    out += ["", f"{c.e('arrow')} <i>{html.escape(c.footer)}</i>"]
  return "\n".join(out)


def t_neon(c: _Ctx, d, desc):
  line = "━" * 14
  out = [f"{line} {c.e('star')} {line}", f"{c.e('crown')} <b>{c.s(d['title'], 'bold')}</b>", line * 2 + "━━", ""]
  out.append(f"▸ {c.label('Genre', 'sans')} : {_tags(d['genres']) or 'N/A'}")
  out.append(f"▸ {c.label('Status', 'sans')} : {html.escape(d['status'] or 'N/A')}")
  if d.get("chapters"):
    out.append(f"▸ {c.label('Chapters', 'sans')} : {d['chapters']}")
  if d.get("formats"):
    out.append(f"▸ {c.label('Format', 'sans')} : {html.escape(d['formats'])}")
  if d.get("source"):
    out.append(f"▸ {c.label('Source', 'sans')} : {html.escape(d['source'])}")
  if desc:
    out += ["", f"<blockquote expandable>{c.e('synopsis')} <b>{c.s('Synopsis', 'sans')}</b>\n{desc}</blockquote>"]
  if c.footer:
    out += ["", f"⚡ <b>{html.escape(c.footer)}</b>"]
  return "\n".join(out)


def t_kawaii(c: _Ctx, d, desc):
  out = ["✧･ﾟ: *✧･ﾟ:*  " + c.e("sparkle") + "  *:･ﾟ✧*:･ﾟ✧",
         f"<b>{c.s(d['title'], 'script')}</b>", "˚ ༘ ೀ⋆｡˚ ", ""]
  out.append(f"{c.e('heart')} {c.s('genre', 'smallcaps')}: <i>{_tags(d['genres']) or 'N/A'}</i>")
  out.append(f"{c.e('heart')} {c.s('status', 'smallcaps')}: <i>{html.escape(d['status'] or 'N/A')}</i>")
  if d.get("chapters"):
    out.append(f"{c.e('heart')} {c.s('chapters', 'smallcaps')}: <i>{d['chapters']}</i>")
  if d.get("formats"):
    out.append(f"{c.e('heart')} {c.s('format', 'smallcaps')}: <i>{html.escape(d['formats'])}</i>")
  if desc:
    out += ["", f"<blockquote expandable><i>{desc}</i></blockquote>"]
  out += ["", "⋆｡°✩ " + (f"<i>{html.escape(c.footer)}</i>" if c.footer else c.s("happy reading", "smallcaps")) + f" {c.e('heart')}"]
  return "\n".join(out)


TEMPLATES = {
  1: ("Elegant Card", t_elegant),
  2: ("Neon Frame", t_neon),
  3: ("Kawaii Minimal", t_kawaii),
}

SAMPLE = {
  "title": "Solo Leveling",
  "genres": ["Action", "Fantasy", "Adventure"],
  "status": "Completed",
  "chapters": 200,
  "formats": "PDF · CBZ",
  "source": "",
  "description": ("Ten years ago, a portal connecting our world to a world of monsters opened. "
                  "Sung Jin-Woo, the weakest of all hunters, gets a second chance to level up "
                  "in a way no one else can."),
}

MAX_VISIBLE = 1000   # Telegram caption limit is 1024; keep a margin


def _clip(text: str, n: int) -> str:
  text = re.sub(r"\s+", " ", text or "").strip()
  return text if len(text) <= n else text[: max(n - 1, 0)].rstrip() + "…"


def render_post(data: dict, template: int = None, premium=None, stylish=None, footer=None) -> str:
  """data: title, genres|genre, status, description, chapters, formats, source."""
  template = template or Vars.POST_TEMPLATE
  _, fn = TEMPLATES.get(int(template), TEMPLATES[1])
  c = _Ctx(premium=premium, stylish=stylish, footer=footer)
  d = dict(data)
  d["title"] = _clip(d.get("title") or "Unknown", 90)
  d["genres"] = _split_genres(d.get("genres", d.get("genre")))
  d["status"] = _clip(d.get("status") or "", 30)
  limit = max(40, int(Vars.POST_DESC_LEN))
  while True:
    desc = html.escape(_clip(d.get("description", ""), limit)) if d.get("description") else ""
    text = fn(c, d, desc)
    if visible_len(text) <= MAX_VISIBLE or limit <= 40:
      return text
    limit = max(40, limit - 40)


def plain_emoji_version(data, template=None):
  """Same post without premium emoji (used if Telegram rejects the custom emoji)."""
  return render_post(data, template, premium=False)
