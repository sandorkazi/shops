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
            return int(self.parsed.find_all("a", class_="pagelink")[-3].text.strip())
        except (ValueError, IndexError, AttributeError):
            return 1

    @staticmethod
    def _parse_listing(parsed: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return parsed.find("div", id="mainContent")

    @staticmethod
    def _parse_grid(listing: bs4.BeautifulSoup) -> bs4.ResultSet:
        return listing.find_all("div", class_="product-search-row")

    @staticmethod
    def _parse_item(base_url: str, item: bs4.BeautifulSoup) -> SingleShopItem:
        s = SingleShopItem()
        try:
            link = item.find("a", class_="productLink")
            try:
                s.title = link.find("img").get("alt").strip()
            except (AttributeError, TypeError, ValueError):
                s.title = ""
            try:
                s.url = base_url + link.get("href").strip()
            except (AttributeError, TypeError, ValueError):
                s.url = ""
            try:
                s.image_url = link.find("img").get("src").strip()
            except (AttributeError, TypeError, ValueError):
                s.image_url = ""
        except (AttributeError, TypeError, ValueError):
            s.title = ""
            s.url = ""
            s.image_url = ""
        try:
            s.stock = item.find("span", class_="card-qty")
            s.stock = " ".join([
                s.stock.text.strip(),
                list(item.find("span", class_="card-qty").next_siblings)[-1].strip(),
            ])
        except (AttributeError, TypeError, ValueError):
            s.stock = ""
        try:
            s.orig_old_price = float(item.find("span", class_="d").find("strike").text.replace("$", "").strip())
        except (AttributeError, TypeError, ValueError):
            s.orig_old_price = np.NaN
        try:
            s.orig_price = float(item.find("b", itemprop="price").text.strip())
        except (AttributeError, TypeError, ValueError):
            s.orig_price = np.NaN
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
            name="coolstuffinccom",
            base_url="https://coolstuffinc.com",
            page_type=Page,
            page_size=30,
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
            (k, f"{self.base_url}/{v}?p={{page}}&s=5")
            for k, v in OrderedDict(
                Sale="main_saleItems.php",
            ).items()
        ))
