# -*- coding: utf-8 -*-
"""Translation of all user-facing texts (GUI, reports, charts).

The source language of the texts is German: every user-facing string in the code is written in German
and passed through ``tr()``. ``tr()`` looks the German text up in the catalog of the current language
(``locales/en.py``, ``locales/es.py``) and falls back to German if no translation exists.

Rules for code that produces user-facing text:

* ``tr("Text mit {platzhalter}", platzhalter=wert)`` translates immediately (use it while drawing or
  rendering, i.e. after the language has been chosen).
* ``N_("Text")`` only marks a string for translation; translate it later with ``tr(text)``.
  Use it for module-level constants such as label tables.
* ``Msg("Text {x}", x=...)`` is a lazily translated message. Analysis results store ``Msg`` objects
  instead of finished strings, so that a result can be shown in another language after switching
  the language without analysing the logs again. ``str(msg)`` gives the text in the current language.
* The first argument of ``tr``, ``N_`` and ``Msg`` must be a string literal - ``tests/test_i18n.py``
  extracts them from the source code and checks that every catalog contains them.
"""

import os
import sys

from .locales import en, es


LANGUAGES = {"de": "Deutsch", "en": "English", "es": "Español"}   # code -> name in that language

SOURCE_LANGUAGE = "de"

CATALOGS = {"de": {}, "en": en.CATALOG, "es": es.CATALOG}

_current = SOURCE_LANGUAGE


def set_language(code):
    """Selects the language for all following ``tr()`` calls. Unknown codes fall back to English."""
    global _current
    _current = code if code in LANGUAGES else "en"


def get_language():
    return _current


def tr(msgid, **kw):
    """Translates msgid into the current language and fills in the placeholders."""
    text = CATALOGS[_current].get(msgid, msgid) if _current != SOURCE_LANGUAGE else msgid
    return text.format(**kw) if kw else text


def N_(msgid):
    """Marks a string for translation without translating it (translate later with ``tr``)."""
    return msgid


class Msg:
    """Message that is translated only when it is converted to text (``str(msg)``)."""

    __slots__ = ("msgid", "kw")

    def __init__(self, msgid, **kw):
        self.msgid = msgid
        self.kw = kw

    def __str__(self):
        return tr(self.msgid, **{k: (str(v) if isinstance(v, (Msg, LazyDate)) else v) for k, v in self.kw.items()})

    def __repr__(self):
        return f"Msg({self.msgid!r})"

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.msgid)

    def __contains__(self, item):
        return item in str(self)

    def startswith(self, prefix):
        return str(self).startswith(prefix)


def fmt_date(d):
    return f"{d:{tr('%d.%m.%Y')}}"


def fmt_datetime(d):
    return f"{d:{tr('%d.%m.%Y %H:%M')}}"


class LazyDate:
    """Date inside a ``Msg``: formatted in the style of the language that is active when it is shown."""

    __slots__ = ("d",)

    def __init__(self, d):
        self.d = d

    def __str__(self):
        return fmt_date(self.d)


def detect_language():
    """Language of the operating system if it is supported, otherwise English."""
    codes = []
    if sys.platform.startswith("win"):
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            codes.append({0x07: "de", 0x09: "en", 0x0A: "es"}.get(lang_id & 0x3FF, ""))
        except Exception:
            pass
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        codes.append(os.environ.get(var, ""))
    try:
        import locale
        codes.append(locale.getlocale()[0] or "")
    except Exception:
        pass
    for c in codes:
        c = c.lower()
        for code, prefixes in (("de", ("de", "german")), ("es", ("es", "spanish")), ("en", ("en", "english"))):
            if c.startswith(prefixes):
                return code
    return "en"
