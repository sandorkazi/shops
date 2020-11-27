import bs4
import json
import os
import pandas as pd
import pickle
import time
from .item import ShopItem, SingleShopItem, ColNames
from selenium import webdriver
from slugify import slugify
from typing import Any, Dict, List


class PageBase:
    """
    Representation of a page (and related caching).
    """

    def __init__(
            self,
            driver: webdriver,
            name: str,
            base_url: str,
            url_name: str,
            date: str,
            url_format: str,
            page: int,
            sleep: float,
            item_limit: int,
            page_size: int,
    ):
        self.name = name
        self.base_url = base_url
        self.url_name = url_name
        self.date = date
        self.url = url_format.format(page=page)
        self.page = page
        self.sleep = sleep
        self.item_limit = item_limit
        self.page_size = page_size

        folder = f"../data/page/{slugify(self.name)}"
        file_name = f"{self.date}_{slugify(self.url)}.pickle"
        try:
            os.mkdir(folder)
        except FileExistsError:
            pass
        self.path = f"{folder}/{file_name}"
        try:
            self._load_raw(driver)
            self.parsed = self._parse_page(self.raw)
            self.listing = self._parse_listing(self.parsed)
            self.grid = self._parse_grid(self.listing)
            self.items = self._safe_parse_items(self.grid, item_limit)
            if self.items:
                self.df = (
                    pd.concat(map(lambda x: x.df(), self.items))
                    .assign(discount=lambda x: x.orig_price / x.orig_old_price * (-100) + 100)
                )
            else:
                self.df = ShopItem.empty_df()
        except Exception as e:
            self.df = (
                SingleShopItem(**{
                    ColNames.error: e,
                    ColNames.etc: dict(
                        path=self.path,
                    ),
                }).df()
            )

    def _safe_parse_items(
            self,
            grid: bs4.ResultSet,
            item_limit: int = 0,
    ) -> List[ShopItem]:
        if item_limit > 0:
            grid = grid[:item_limit]
        items = []
        for item_raw in grid:
            item = self._parse_item(base_url=self.base_url, item=item_raw)
            item[ColNames.raw] = item_raw
            items.append(item)
        return items

    def _save_raw(self):
        assert self.raw is not None, "Can't save before the value is set"
        if self.path is not None:
            with open(self.path, "wb") as fout:
                pickle.dump(self.raw, fout)

    def _load_raw(self, driver):
        assert not hasattr(self, "raw") or self.raw is None, "Can't load after the value is set"
        if self.path is not None and os.path.exists(self.path) and os.path.isfile(self.path):
            with open(self.path, "rb") as fin:
                self.raw = pickle.load(fin)
        else:
            driver.get(self.url)
            time.sleep(self.sleep)
            self.raw = driver.page_source
            self._save_raw()

    @staticmethod
    def _parse_page(raw: str) -> Any:
        raise NotImplementedError()

    @property
    def max_page(self) -> int:
        raise NotImplementedError()

    @staticmethod
    def _parse_listing(parsed: Any) -> Any:
        raise NotImplementedError()

    @staticmethod
    def _parse_grid(listing: Any) -> Any:
        raise NotImplementedError()

    @staticmethod
    def _parse_item(base_url: str, item: Any) -> ShopItem:
        raise NotImplementedError()


class JSONPageBase(PageBase):
    """
    Representation of a JSON page.
    """

    @staticmethod
    def _parse_page(raw: str) -> Dict[str, Any]:
        return json.loads(raw)

    @staticmethod
    def _parse_listing(parsed: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

    @staticmethod
    def _parse_grid(listing: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

    @staticmethod
    def _parse_item(base_url: str, item: Dict[str, Any]) -> ShopItem:
        raise NotImplementedError()


class HTML5PageBase(PageBase):
    """
    Representation of a HTML5 page.
    """

    @staticmethod
    def _parse_page(raw: str) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(
            raw,
            features='html5lib',
        )

    @staticmethod
    def _parse_listing(parsed: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        raise NotImplementedError()

    @staticmethod
    def _parse_grid(listing: bs4.BeautifulSoup) -> bs4.ResultSet:
        raise NotImplementedError()

    @staticmethod
    def _parse_item(base_url: str, item: bs4.BeautifulSoup) -> ShopItem:
        raise NotImplementedError()
