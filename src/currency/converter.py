#!/usr/bin/env python
#  coding=utf-8

import pandas as pd

from typing import Union, Any
from currency_converter import CurrencyConverter

cc = CurrencyConverter()


def convert_value(
        value: Any,
        rate: float,
) -> Union[float, None]:
    try:
        return float(value) * rate
    except (TypeError, ValueError):
        return None


def get_rate(
        from_currency: str,
        to_currency: str,
) -> float:
    return round(cc.convert(1, from_currency, to_currency), 3)


def convert_series(
        series: pd.Series,
        rate: float,
) -> pd.Series:
    return (
        series
        .map(lambda x: convert_value(x, rate=rate))
    )
