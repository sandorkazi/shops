#!/usr/bin/env python
#  coding=utf-8

import click
import logging

from datetime import datetime
from importlib import import_module
from importlib import util as import_util


@click.command()
@click.argument("url")
@click.option("-t/ ", "--test-mode/--normal-mode", default=False)
@click.option(" /-p", "--public/--private", default=True)
@click.option("-d", "--date-override", default=None)
def cmd(url, test_mode, public, date_override):
    logger = logging.Logger(name="shops")
    url = url.strip("http://").strip("https://").strip("www.")
    url = url.split("/")[0]
    module_name = ''.join((i for i in url if i.isalnum()))
    if test_mode:
        test_params = dict(
            url_limit=2,
            page_limit=2,
            item_limit=2,
            headless=True,
        )
    else:
        test_params = dict()
    logger.info("Downloading...")
    shop_module = import_util.find_spec(f"shops.{module_name}")
    if shop_module is not None:
        shop_module = import_module(f"shops.{module_name}")
        # noinspection PyUnresolvedReferences
        shop = shop_module.Shop(
            date=date_override or datetime.strftime(datetime.now(), "%Y%m%d"),
            **test_params,
        )
    else:
        logger.error("No such shop implemented.")
        raise NotImplementedError()
    if public:
        logger.info("Uploading...")
        shop.upload()


if __name__ == "__main__":
    cmd()
