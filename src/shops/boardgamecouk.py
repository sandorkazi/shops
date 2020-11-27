import bs4
import numpy as np
from collections import OrderedDict
from scraper import HTML5PageBase
from scraper import ShopBase
from scraper import SingleShopItem


class Page(HTML5PageBase):

    @property
    def max_page(self) -> int:
        try:
            return int(self.parsed.find(class_='bpf-filter-paging-links').findAll("a")[-2].get("data-page"))
        except (AttributeError, ValueError, TypeError, IndexError):
            return 1

    @staticmethod
    def _parse_listing(parsed: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return parsed.find(class_='zg-products-list')

    @staticmethod
    def _parse_grid(listing: bs4.BeautifulSoup) -> bs4.ResultSet:
        return listing.findAll(class_='zg-product')

    @staticmethod
    def _parse_item(base_url: str, item: bs4.BeautifulSoup) -> SingleShopItem:
        s = SingleShopItem()
        try:
            s.title = item.find(class_='zg-product-title').text.strip()
        except (AttributeError, TypeError, ValueError):
            s.title = ""
        try:
            s.stock = item.find(class_='zg-product-notice').text
        except (AttributeError, TypeError, ValueError):
            s.stock = ""
        try:
            price_box = item.find(class_="zg-product-prices")
            try:
                s.orig_price = (
                    price_box
                    .find(class_="zg-product-price")
                    .find("span")
                    .text
                    .replace("£", "")
                    .replace(" ", "")
                )
                s.orig_price = float(s.orig_price)
            except (AttributeError, TypeError, ValueError):
                s.orig_price = np.NaN
            try:
                s.orig_old_price = (
                    price_box
                    .find(class_="zg-product-rrp")
                    .find("span")
                    .text
                    .replace("£", "")
                    .replace(" ", "")
                )
                s.orig_old_price = float(s.orig_old_price)
            except (AttributeError, TypeError, ValueError):
                s.orig_old_price = np.NaN
        except (AttributeError, TypeError, ValueError):
            s.orig_price = np.NaN
            s.orig_old_price = np.NaN
        try:
            image_box = item.find(class_='zg-product-image-container')
            try:
                s.url = image_box.find("a").get("href")
            except (AttributeError, TypeError, ValueError):
                s.url = ""
            try:
                s.image_url = image_box.find("img").get("src")
            except (AttributeError, TypeError, ValueError):
                s.image_url = ""
        except (AttributeError, TypeError, ValueError):
            s.url = ""
            s.image_url = ""
        return s


class Shop(ShopBase):

    def __init__(
            self,
            date: str,
            url_limit: int = 0,
            page_limit: int = 0,
            item_limit: int = 0,
            headless: bool = True,
    ):
        super().__init__(
            name="boardgamecouk",
            base_url="https://board-game.co.uk",
            page_type=Page,
            page_size=80,
            currency="GBP",
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
            (k, f"{self.base_url}/category/{v}/?count={self.page_size}&page={{page}}")
            for k, v in OrderedDict(
                boardgames="board-games",
                tradingcardgames="trading-card-games",
                # miniatures="miniatures",
                # puzzles="puzzles",
                accessories="accessories",
                # books="books",
                # dvds="dvds",
                # gaming="video-games",
            ).items()
        ))
