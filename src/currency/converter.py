"""
Convert between currencies.
"""

import numpy as np
import pandas as pd
from currency_converter import CurrencyConverter

__cc = CurrencyConverter()
"""Currency converter object"""


def convert_value(
        value,
        rate: float,
) -> float:
    """
    Convert a value using a rate. Drop everything non-numeric from the string representation first.
    :param value: value to convert (string or float)
    :param rate: rate to multiply by
    :return: converted value or np.NaN
    """
    try:
        value = "".join([
            c
            for c in str(value).replace(",", ".")
            if c in "0123456789."
        ])
        return float(value) * rate
    except (TypeError, ValueError):
        return np.NaN


def get_rate(
        from_currency: str,
        to_currency: str,
) -> float:
    """
    Get conversion between currencies.
    :param from_currency: from
    :param to_currency: to
    :return: conversion rate
    """
    return round(__cc.convert(1, from_currency, to_currency), 3)


def convert_series(
        series: pd.Series,
        rate: float,
) -> pd.Series:
    """
    Convert series (multiply by rate) from one currency to the other.
    :param series: series to convert
    :param rate: rate to multiply by
    :return: converted series
    """
    return (
        series
        .map(lambda x: convert_value(x, rate=rate))
    )
