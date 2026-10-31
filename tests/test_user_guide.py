# -*- coding: utf-8 -*-
"""The user guides (docs/user-guide_<language>.md and .pdf) are complete and their screenshots show something.

The PDFs are attached to every release, so a guide with a missing or blank screenshot must never get that far.
Screenshots taken while the screen is locked or switched off come out as one flat colour; such an image has (almost)
no contrast, which is what this test looks for. Pillow is installed with matplotlib.
"""

import re

import pytest
from PIL import Image, ImageStat

from helpers import ROOT

DOCS = ROOT / "docs"
LANGUAGES = ("en", "de")
IMAGE_LINK = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
# grey-level standard deviation below which a picture counts as blank; real screenshots of the app are above 30
MIN_CONTRAST = 5.0
REGENERATE_HINT = "Take the screenshots again with the screen unlocked, then create the PDFs again."


def guide_images(language):
    """Paths of the images the guide of a language links to, in the order they appear."""
    text = (DOCS / ("user-guide_%s.md" % language)).read_text(encoding="utf-8")
    return [DOCS / link for link in IMAGE_LINK.findall(text)]


@pytest.mark.parametrize("language", LANGUAGES)
def test_guide_and_pdf_exist(language):
    assert (DOCS / ("user-guide_%s.md" % language)).is_file()
    assert (DOCS / ("user-guide_%s.pdf" % language)).stat().st_size > 0


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_screenshot_exists_and_is_not_blank(language):
    images = guide_images(language)
    assert images, "the guide has no screenshots"
    missing = [path.name for path in images if not path.is_file()]
    assert not missing, "missing screenshots: %s" % missing
    blank = []
    for path in images:
        with Image.open(path) as image:
            contrast = ImageStat.Stat(image.convert("L")).stddev[0]
        if contrast < MIN_CONTRAST:
            blank.append("%s (contrast %.1f)" % (path.name, contrast))
    assert not blank, "blank screenshots: %s. %s" % (blank, REGENERATE_HINT)


def test_both_languages_show_the_same_screenshots():
    names = {language: [path.name for path in guide_images(language)] for language in LANGUAGES}
    assert names["en"] == names["de"]
