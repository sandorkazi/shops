"""
milan-spiele.de
"""

import bs4
import numpy as np
import re
from collections import OrderedDict
from scraper import HTML5PageBase
from scraper import ShopBase
from scraper import SingleShopItem
from typing import List, Tuple


class Page(HTML5PageBase):
    """
    Page representation.
    """

    stock_regex = re.compile("images/.*[.]gif")
    """Regex for stock status check."""

    count_regex = re.compile("Artikel [0-9]* bis [0-9]*[(]von ([0-9]*)[)]")
    """Regex to find total count."""

    @property
    def max_page(self) -> int:
        """The number of the last page."""
        try:
            total = int(
                self.count_regex.findall(self.parsed.find(class_="smallText").text.strip())[0]
            )
            return (total - 1) // self.page_size + 1
        except (AttributeError, TypeError, ValueError, IndexError):
            return 1

    @staticmethod
    def _parse_listing(parsed: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return parsed.find("table", class_="productListing")

    @staticmethod
    def _parse_grid(listing: bs4.BeautifulSoup) -> bs4.ResultSet:
        return listing.find_all("tr", class_="productListing-odd")

    @staticmethod
    def _parse_item(base_url: str, item: bs4.BeautifulSoup) -> SingleShopItem:
        s = SingleShopItem()
        try:
            s.title = item.find("strong").text.strip()
        except (AttributeError, TypeError, ValueError):
            s.title = None
        try:
            x = item.find("img", src=re.compile("images/.*[.]gif"))
            s.stock = f"{x.get('alt').strip()} - {x.get('src').replace('images/','').replace('.gif','')}"
        except (AttributeError, TypeError, ValueError):
            s.stock = None
        try:
            s.url = item.find("a").get("href").strip()
        except (AttributeError, TypeError, ValueError):
            s.url = None
        try:
            s.image_url = item.find("img").get("src").replace("/imagecache/", "/").strip()
        except (AttributeError, TypeError, ValueError):
            s.image_url = None
        try:
            prices = item.find_all("nobr")
            try:
                s.orig_price = float(prices[-1].text.replace(",", ".").replace("€", "").strip())
            except (AttributeError, TypeError, ValueError):
                s.orig_price = np.NaN
            try:
                # noinspection PyUnresolvedReferences
                s.orig_old_price = float(prices[-2].text.replace(",", ".").replace("€", "").strip())
            except (AttributeError, TypeError, ValueError):
                s.orig_old_price = np.NaN
        except (AttributeError, TypeError, ValueError):
            s.orig_price = np.NaN
            s.orig_old_price = np.NaN
        return s


class SubPage(HTML5PageBase):
    """
    Subpage representation to look up the URL we should normally walk.
    """

    @property
    def max_page(self) -> int:
        """The number of the last page."""
        return 1

    @staticmethod
    def _parse_listing(parsed: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return parsed.find("td", text="Kategorien").find_parent("tbody").find_all("tr")[1]

    @staticmethod
    def _parse_grid(listing: bs4.BeautifulSoup) -> bs4.ResultSet:
        try:
            return listing.find_all("div")[1].find_all("a")
        except (AttributeError, TypeError, ValueError, IndexError):
            return bs4.ResultSet([])

    @staticmethod
    def _parse_item(base_url: str, item: bs4.BeautifulSoup) -> SingleShopItem:
        s = SingleShopItem()
        try:
            s.title = item.text.strip()
        except (AttributeError, TypeError):
            s.title = ""
        try:
            s.url = item.get("href").strip()
        except (AttributeError, TypeError):
            s.url = ""
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
            name="milanspielede",
            base_url="https://milan-spiele.de",
            page_type=Page,
            page_size=250,
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
        leaf_pages = [
            self._url_formats_from(
                title=title,
                url=f"{self.base_url}/{name}",
            )
            for title, name in OrderedDict(
                News="neuheiten-c-102.html",
                Offers="angebote-c-103.html",
                GameWorlds="spielewelten-c-752.html",
                Games="spiele-c-82.html",
                Accessories="zubehr-c-868.html",
                Used="gebraucht-c-104.html",

                # Recommendations="empfehlungen-c-555.html",
                # Puzzle="puzzle-c-929.html",
                # Awards="auszeichnungen-c-105.html",
            ).items()
        ]
        return OrderedDict(
            sum(leaf_pages, [])
        )

    def _url_formats_from(
            self,
            title: str,
            url: str,
    ) -> List[Tuple[str, str]]:
        sub_page = SubPage(
            driver=self.driver,
            name=self.name,
            base_url=self.base_url,
            url_name=self.name,
            date=self.date,
            url_format=url,
            page=1,
            sleep=self.sleep,
            item_limit=0,
            page_size=self.page_size,
        )
        if sub_page.df.empty:
            return [(
                title,
                f"{url}?page={{page}}&sort=1a&perPage={self.page_size}",
            )]
        else:
            return (
                sub_page.df
                .assign(
                    title=lambda df: df.title.map(lambda x: f"{title}|{x}"),
                    url_format=lambda df: df.url.map(
                        lambda _url: f"{_url}?page={{page}}&sort=1a&perPage={self.page_size}",
                    ),
                )
                [["title", "url_format"]]
                .values
                .tolist()
            )
