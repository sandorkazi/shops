"""
miniaturemarket.com
"""

import bs4
import numpy as np
from collections import OrderedDict
from scraper import HTML5PageBase
from scraper import ShopBase
from scraper import SingleShopItem


PAGE_SIZE_MULTIPLIER = 32
"""Multipler to set startAt value instead of page (but use the same implementation)."""


class Page(HTML5PageBase):
    """
    PAgE representation.
    """

    def __init__(
        self,
        page: int,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            page=(page-1) * PAGE_SIZE_MULTIPLIER,
            **kwargs,
        )

    @property
    def max_page(self) -> int:
        """The number of the last page."""
        try:
            return int(self.parsed.find_all("a", href="#")[-1].text.strip())
        except (ValueError, IndexError, AttributeError):
            return 1

    @staticmethod
    def _parse_listing(parsed: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return parsed.find("div", class_="product-grid")

    @staticmethod
    def _parse_grid(listing: bs4.BeautifulSoup) -> bs4.ResultSet:
        return listing.find_all("div", class_="item")

    @staticmethod
    def _parse_item(base_url: str, item: bs4.BeautifulSoup) -> SingleShopItem:
        s = SingleShopItem()
        try:
            link = item.find("a", class_="product-image")
            try:
                s.title = link.get("title").strip()
            except (AttributeError, TypeError, ValueError):
                s.title = ""
            try:
                s.url = link.get("href").strip()
            except (AttributeError, TypeError, ValueError):
                s.url = ""
            try:
                s.image_url = "http:" + link.find("img").get("src").strip()
            except (AttributeError, TypeError, ValueError):
                s.image_url = ""
        except (AttributeError, TypeError, ValueError):
            s.title = ""
            s.url = ""
            s.image_url = ""
        try:
            s.stock = item.find(class_="availability").text.strip()
        except (AttributeError, TypeError, ValueError):
            s.stock = ""
        try:
            prices = item.find_all("span", class_="price")[::-1]
            s.orig_price, s.orig_old_price, *_ = *prices, None, None
            try:
                s.orig_price = float(s.orig_price.text.replace("$", "").strip())
            except (AttributeError, TypeError, ValueError):
                s.orig_price = np.NaN
            try:
                # noinspection PyUnresolvedReferences
                s.orig_old_price = float(s.orig_old_price.text.replace("$", "").strip())
            except (AttributeError, TypeError, ValueError):
                s.orig_old_price = np.NaN
        except (AttributeError, TypeError, ValueError):
            s.orig_price = np.NaN
            s.orig_old_price = np.NaN
        return s


class Shop(ShopBase):
    """
    Shop representation.
    """

    def __init__(
            self,
            date: str,
            url_limit: int = 0,
            page_limit: int = 0,
            item_limit: int = 0,
            headless: bool = True,
    ):
        super().__init__(
            name="miniaturemarketcom",
            base_url="https://miniaturemarket.com",
            page_type=Page,
            page_size=PAGE_SIZE_MULTIPLIER,
            currency="USD",
            dimensions=(1600, 3000),
            sleep=0.1,
            spreadsheet="BGShops",
            date=date,
            url_limit=url_limit,
            page_limit=page_limit,
            item_limit=item_limit,
            headless=headless,
        )

    def _url_formats(self) -> OrderedDict:
        return OrderedDict((
            (k, f"{self.base_url}/{v}?start={{page}}")
            for k, v in OrderedDict(
                Deal="deals.html",
                BoardGames="board-games.html",
                Accessories="accessories.html",
            ).items()
        ))
