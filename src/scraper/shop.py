import pandas as pd
from .item import ColNames
from .page import PageBase
from collections import OrderedDict
from currency import get_rate, convert_series
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from slugify import slugify
from tqdm import tqdm
from typing import Any, Tuple, Type
from uploader.sheets import GSpreadWrapper


BASE_CURRENCY = "HUF"


class ShopBase:
    """
    Representation of a shop.
    """

    def __init__(
            self,
            name: str,
            base_url: str,
            date: str,
            page_type: Type[PageBase],
            page_size: int,
            currency: str,
            dimensions: Tuple[int, int],
            sleep: float,
            spreadsheet: str = None,
            *,
            url_limit: int = 0,
            page_limit: int = 0,
            item_limit: int = 0,
            headless: bool = True,
    ):
        self.spreadsheet = spreadsheet
        self.name = name
        self.base_url = base_url
        self.date = date

        self.path = f"../data/shop/{self.date}_{slugify(self.name)}_LIMIT_{url_limit}_{page_limit}_{item_limit}.xlsx"
        self.page_type = page_type
        self.page_size = page_size
        self.currency = currency
        self.rate = get_rate(currency, BASE_CURRENCY)
        self.driver = self._new_driver(
            dimensions,
            headless,
        )
        self.sleep = sleep
        url_formats = self._url_formats()
        if url_limit > 0:
            url_formats = {
                k: url_formats[k]
                for i, k in enumerate(url_formats)
                if i < url_limit
            }
        self.pages = OrderedDict(
            (
                url_name,
                self._get_pages(
                    driver=self.driver,
                    name=name,
                    base_url=base_url,
                    url_name=url_name,
                    date=self.date,
                    url_format=url_format,
                    page_type=page_type,
                    sleep=sleep,
                    page_limit=page_limit,
                    item_limit=item_limit,
                    page_size=page_size,
                ),
            ) for url_name, url_format in url_formats.items()
        )
        self.df = self._parse_df()
        self.df.to_excel(self.path, index=False)
        self.driver.close()

    @staticmethod
    def _new_driver(
            dimensions: Tuple[int, int],
            headless: bool,
    ):
        options = Options()
        options.headless = headless
        driver = webdriver.Chrome(
            options=options,
            keep_alive=True,
        )
        driver.set_window_size(*dimensions)
        return driver

    def _url_formats(self) -> OrderedDict:
        raise NotImplementedError()

    @classmethod
    def _get_pages(
            cls,
            driver: webdriver,
            name: str,
            base_url: str,
            url_name: str,
            date: str,
            url_format: str,
            page_type: Type[PageBase],
            sleep: float,
            page_limit: int,
            item_limit: int,
            page_size: int,
    ) -> Any:
        pages = []
        page1 = page_type(
            driver=driver,
            name=name,
            base_url=base_url,
            url_name=url_name,
            date=date,
            url_format=url_format,
            page=1,
            sleep=sleep,
            item_limit=item_limit,
            page_size=page_size,
        )
        pages.append(page1)
        max_page = page1.max_page
        if page_limit < 1:
            page_limit = max_page
        page_range = iter(tqdm(range(page_limit+1)))
        next(page_range)
        for p in page_range:
            if p == 1:
                continue
            page = page_type(
                driver=driver,
                name=name,
                base_url=base_url,
                url_name=url_name,
                date=date,
                url_format=url_format,
                page=p,
                sleep=sleep,
                item_limit=item_limit,
                page_size=page_size,
            )
            pages.append(page)
        return pages

    def _parse_df(self) -> pd.DataFrame:
        df = (
            pd
            .concat(
                [
                    page.df.assign(group=page_group_name)
                    for page_group_name, page_group in self.pages.items()
                    for page in page_group
                ]
            )
            .reset_index(drop=True)
            .assign(
                converted_price=lambda x: round(convert_series(x.orig_price, rate=self.rate), 3),
                converted_old_price=lambda x: round(convert_series(x.orig_old_price, rate=self.rate), 3),
                conversion_rate=self.rate,
                currency=self.currency,
            )
            .sort_values(["discount", "title"], ascending=[0, 1])
        )
        return df

    def upload(self):
        assert self.spreadsheet is not None, "Can't upload when spreadsheet was not set."
        uploader = GSpreadWrapper(
            spreadsheet=self.spreadsheet,
        )
        uploader.set_value_by_lookup(
            sheet='TS',
            lookup_value=self.base_url,
            lookup_index=0,
            value_index=1,
            value='In progress...',
        )
        (
            uploader.upload(
                sheet=self.name,
                df=self.df.drop([ColNames.raw, ColNames.error], axis=1)
            )
        )
        uploader.set_value_by_lookup(
            sheet='TS',
            lookup_value=self.base_url,
            lookup_index=0,
            value_index=1,
            value=self.date,
        )
