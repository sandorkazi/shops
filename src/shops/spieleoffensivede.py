"""
spieleoffensive.de
"""

import bs4
import numpy as np
import re
from collections import OrderedDict
from scraper import HTML5PageBase
from scraper import ShopBase
from scraper import SingleShopItem


class Page(HTML5PageBase):
    """
    Page representation.
    """

    def __init__(
            self,
            page: int,
            *args,
            **kwargs,
    ):
        super().__init__(
            *args,
            page=page-1,
            **kwargs,
        )

    @property
    def max_page(self) -> int:
        """The number of the last page."""
        try:
            return int(self.parsed.find("div", class_="nav").find_all("a")[-2].text.strip())
        except (IndexError, ValueError, AttributeError, TypeError):
            return 1

    @staticmethod
    def _parse_listing(parsed: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return parsed.find("ul", class_="ala")

    @staticmethod
    def _parse_grid(listing: bs4.BeautifulSoup) -> bs4.ResultSet:
        return listing.find_all("li", class_="ala")

    @staticmethod
    def _parse_item(base_url: str, item: bs4.BeautifulSoup) -> SingleShopItem:
        s = SingleShopItem()
        s.title = lambda: item.find("a", class_="alamain").find("font").text.strip()
        s.stock = lambda: item.find_all("a", class_="kbw")[-1].get("title").strip()
        s.url = lambda: f'{base_url}{item.find("a", class_="alamain").get("href").strip()}'
        s.image_url = lambda: f'{base_url}{item.find("img").get("src").strip()}'
        s.orig_price = lambda: (
            float(
                ".".join(
                    map(lambda x: x.text.strip(), item.find("div", class_="ala").find_all("span", class_=""))
                )
            )
        )
        s.orig_old_price = lambda: (
            float(s.orig_price) * 100 / (100-int(item.find("img").get("src").split("?r=")[1].split("&")[0]))
        )
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
            name="spieleoffensivede",
            base_url="https://www.spiele-offensive.de",
            page_type=Page,
            page_size=50,
            currency="EUR",
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
        return OrderedDict(
                All="https://www.spiele-offensive.de/Gesellschaftsspiele-{page}.html",
        )
