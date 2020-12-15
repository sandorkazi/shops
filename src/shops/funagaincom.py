"""
funagain.com
"""

import bs4
import numpy as np
from collections import OrderedDict
from scraper import HTML5PageBase
from scraper import ShopBase
from scraper import SingleShopItem


class Page(HTML5PageBase):
    """
    Page representation.
    """

    @property
    def max_page(self) -> int:
        """The number of the last page."""
        try:
            return int(self.parsed.find(class_="pagination-custom").find_all("a")[-2].text.strip())
        except (ValueError, IndexError, AttributeError):
            return 1

    @staticmethod
    def _parse_listing(parsed: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return parsed

    @staticmethod
    def _parse_grid(listing: bs4.BeautifulSoup) -> bs4.ResultSet:
        return listing.find_all(class_="product-grid-item")

    @staticmethod
    def _parse_item(base_url: str, item: bs4.BeautifulSoup) -> SingleShopItem:
        s = SingleShopItem()
        try:
            s.title = item.find("p").text.strip()
        except (AttributeError, TypeError, ValueError):
            s.title = ""
        try:
            s.stock = "Unavailable" if item.find("span", text="Unavailable") else "Available"
        except (AttributeError, TypeError, ValueError):
            s.stock = ""
        try:
            price_box = item.find(class_="product-item--price")
            orig_price, _, orig_old_price, *_ = *price_box.find_all("small"), None, None, None
            try:
                s.orig_price = float(orig_price.text.replace("$", "").strip()) / 100
            except (AttributeError, TypeError, ValueError):
                s.orig_price = np.NaN
            try:
                # noinspection PyUnresolvedReferences
                s.orig_old_price = float(orig_old_price.text.replace("$", "").strip()) / 100
            except (AttributeError, TypeError, ValueError):
                s.orig_old_price = np.NaN
        except (AttributeError, TypeError, ValueError):
            s.orig_price = np.NaN
            s.orig_old_price = np.NaN
        try:
            s.url = base_url + item.get("href").strip().split("?")[0]
        except (AttributeError, TypeError, ValueError):
            s.url = np.NaN
        try:
            s.image_url = "https:" + item.find("img").get("srcset").split(",")[-1].split("?")[0].strip(" ")
        except (AttributeError, TypeError, ValueError):
            s.image_url = ""
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
            name="funagaincom",
            base_url="https://funagain.com",
            page_type=Page,
            page_size=24,
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
            (k, f"{self.base_url}/collections/{v}?page={{page}}")
            for k, v in OrderedDict(
                BoardGames="board-games",
                CardGames="card-games",
                Accessories="accessories",
            ).items()
        ))
