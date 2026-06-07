"""Holds template variables for HTML/JS/CSS."""

import math
from enum import StrEnum

from dixit.utils import url_join


class Labels:
    """Text labels."""

    TITLE = "Dixit"
    NEW_GAME = "New Game"
    HIDE_GAME = "Hide Game"
    DEFAULT_TEXT = "Say something!"


class WebPaths:
    """Client-side paths to resource directories."""

    STATIC = "static"
    IMAGES = url_join(STATIC, "images")
    JS = url_join(STATIC, "js")
    CSS = url_join(STATIC, "css")
    CARDS = url_join(STATIC, "cards")
    SMILIES = url_join(IMAGES, "smilies")
    JQUERY_UI = url_join(JS, "jquery-ui-1.10.4")


class Images:
    """Client-side paths to images."""

    BANNER = url_join(WebPaths.IMAGES, "banner.png")
    BUNNY_READY = url_join(WebPaths.IMAGES, "bunnyready.png")
    BUNNY_RUN = url_join(WebPaths.IMAGES, "bunnyrun.png")
    THINKING = url_join(WebPaths.IMAGES, "thinking.gif")
    CARD_BACK = url_join(WebPaths.IMAGES, "cardback.png")
    VOTE_TOKEN = url_join(WebPaths.IMAGES, "votetoken.png")
    YOUR_TURN = url_join(WebPaths.IMAGES, "arrow.ico")
    ICON_ACTIVE = url_join(WebPaths.IMAGES, "bunnyicongreen.png")
    ICON_AWAY = url_join(WebPaths.IMAGES, "bunnyiconyellow.png")
    ICON_ASLEEP = url_join(WebPaths.IMAGES, "bunnyicongrey.png")


class Sizes:
    """Display sizes for images."""

    PIECE = 45
    BUNNY_PICKER = 70
    CARD_WIDTH = 250
    CARD_HEIGHT = 380
    YOUR_TURN = 24
    TOKEN = 80


class BunnyPalette(StrEnum):
    """Bunny colours to choose from."""

    LIGHT_PURPLE = "d499ff"
    PURPLE = "a41bf3"
    RED = "c52828"
    PINK = "f299b1"
    ORANGE = "e59100"
    YELLOW = "e2e05d"
    BROWN = "a18332"
    LIGHT_GREEN = "b5e8c4"
    GREEN = "66bd28"
    DARK_GREEN = "12751b"
    BLUE = "214ddc"
    CYAN = "1bbdbf"
    WHITE = "fafafa"
    LIGHT_GRAY = "b5b5b5"
    DARK_GRAY = "6e6e6e"
    BLACK = "222222"

    @classmethod
    def is_colour(cls, cid):
        """Determines if the given colour id is valid."""
        return cid in cls._value2member_map_

    @classmethod
    def grid(cls):
        """Arranges the colours into near-square rows for display."""
        colours = list(cls)
        cols = math.ceil(math.sqrt(len(colours)))
        return [colours[i : i + cols] for i in range(0, len(colours), cols)]
