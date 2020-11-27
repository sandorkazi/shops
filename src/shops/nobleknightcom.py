import bs4
import numpy as np
import re
from collections import OrderedDict
from scraper import HTML5PageBase
from scraper import ShopBase
from scraper import CompositeShopItem
from typing import Pattern


Regex = Pattern[str]


class NobleKnightPriceParser:

    price = re.compile(" Price *[$]([0-9.]*)")
    old_price = re.compile("Was *[$]([0-9.]*)")
    msrp = re.compile("MSRP *[$]([0-9.]*)")

    @staticmethod
    def get_price(item: bs4.BeautifulSoup, regex: Regex) -> float:
        try:
            return float(regex.findall(item.text)[0])
        except (IndexError, ValueError):
            return np.NaN


class Page(HTML5PageBase):

    @property
    def max_page(self) -> int:
        try:
            return int(self.parsed.findAll(class_='page-link')[-2].text)
        except ValueError:
            return 1

    @staticmethod
    def _parse_listing(parsed: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return parsed.find(class_='listing-col')

    @staticmethod
    def _parse_grid(listing: bs4.BeautifulSoup) -> bs4.ResultSet:
        return listing.findAll(class_='product-card')

    @staticmethod
    def _parse_item(base_url: str, item: bs4.BeautifulSoup) -> CompositeShopItem:
        s = CompositeShopItem()
        try:
            s.title = item.find(class_='name').text.strip()
        except (AttributeError, TypeError, ValueError):
            s.title = ""
        try:
            item_box = item.find(class_="conditions")
            try:
                s.stock = [i.text for i in item_box.findAll(class_="condition-value")]
            except (AttributeError, TypeError, ValueError):
                s.stock = ""
            try:
                price_boxes = item_box.findAll(class_="price-wrapper")
                try:
                    s.orig_price = []
                    s.orig_old_price = []
                    s.msrp = []
                    nkpp = NobleKnightPriceParser
                    for price_box in price_boxes:
                        s.orig_price.append(nkpp.get_price(price_box, nkpp.price))
                        s.orig_old_price.append(nkpp.get_price(price_box, nkpp.old_price))
                        s.msrp.append(nkpp.get_price(price_box, nkpp.msrp))
                except (AttributeError, TypeError, ValueError):
                    s.orig_price = np.NaN
                    s.orig_old_price = np.NaN
                    s.msrp = np.NaN
            except (AttributeError, TypeError, ValueError):
                s.orig_price = np.NaN
                s.orig_old_price = np.NaN
        except (AttributeError, TypeError, ValueError):
            s.stock = ""
        try:
            image_box = item.find(class_='image-col')
            try:
                s.url = base_url + image_box.get("href")
            except (AttributeError, TypeError, ValueError):
                s.url = ""
            try:
                s.image_url = (
                    image_box
                    .find(class_="bg-img-container")
                    .get("style")
                    .replace("background-image: url('", "")
                    .replace("');", "")
                )
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
            name="nobleknightcom",
            base_url="https://nobleknight.com",
            page_type=Page,
            page_size=100,
            currency="USD",
            dimensions=(1600, 6000),
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
            (k, f"{self.base_url}/MC/{v}?PageSize={self.page_size}&PageNumber={{page}}#pf")
            for k, v in OrderedDict(
                boardgames="BoardGames",
                accessories="Dice-And-Supplies",
                # ccg="CCGs",
                # rpg="Role-Playing-Games",
                # wargames="WarGames",
                # miniatures="Miniatures-And-Games",
                # historical_miniatures="Historical-Miniatures",
            ).items()
        ))
