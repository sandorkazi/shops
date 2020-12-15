"""
Google sheet tools.
"""

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from typing import Any


SAC_FILE = '/home/masu/.ssh/bgshops.json'
"""`ServiceAccountCredentials` file location for Google Spreadsheets."""


class GSpreadWrapper:
    """
    Manage data in Google sheets using `pandas` `DataFrame`s.
    """

    def __init__(
            self,
            spreadsheet: str
    ):
        self._sac = SAC_FILE
        self._spreadsheet = spreadsheet
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self._sac, scope)
        gc = gspread.authorize(credentials)
        self.__gc = gc
        self.__ss = gc.open(self._spreadsheet)

    def upload(self, sheet: str, df: pd.DataFrame):
        """
        Upload an entire sheet of data.
        :param sheet: worksheet name
        :param df: `pandas` `DataFrame` to upload
        """
        if len(df) == 0:
            raise ValueError('Won\'t update with empty set')
        ws = self.__ss.worksheet(sheet)
        ws.clear()
        col_cnt = len(df.columns)
        max_col = chr(ord('A') + col_cnt - 1)
        max_row = len(df) + 1
        ws.resize(max_row, col_cnt)
        header = ws.range('A1:{}1'.format(max_col))
        for cell, col in zip(header, df.columns):
            cell.value = col
        ws.update_cells(header)
        data = ws.range('A2:{}{}'.format(max_col, max_row))
        df = df.fillna('').astype(str)
        for i, cell in enumerate(data):
            cell.value = df.iloc[i // col_cnt, i % col_cnt]
        ws.update_cells(data)

    def download(self, sheet: str) -> pd.DataFrame:
        """
        Download an entire sheet of data.
        :param sheet: worksheet name
        :return: `pandas` `DataFrame` from the data
        """
        ws = self.__ss.worksheet(sheet)
        return pd.DataFrame(ws.get_all_records())[ws.row_values(1)]

    def set_value(self, sheet: str, row: int, column: int, value: Any):
        """
        Set a value in a cell.
        :param sheet: worksheet name
        :param row: row index (0..)
        :param column: column index (0..)
        :param value: value to set
        """
        self.__ss.worksheet(sheet).update_cell(row + 1, column + 1, value)

    def get_value(self, sheet: str, row: int, column: int) -> Any:
        """
        Set a value in a cell.
        :param sheet: worksheet name
        :param row: row index (0..)
        :param column: column index (0..)
        :return: value in cell
        """
        return self.__ss.worksheet(sheet).cell(row + 1, column + 1)

    def set_value_by_lookup(
            self,
            sheet: str,
            *,
            axis: int = 1,
            lookup_value: str,
            lookup_index: int,
            value_index: int,
            value: Any,
    ):
        """
        Set a value based on vertical or horizontal lookup.
        :param sheet: worksheet name
        :param axis: vertical (1) or horizontal (0) lookup (default: 1)
        :param lookup_value: value to lookup
        :param lookup_index: row or column index (0..) to lookup in
        :param value_index: row or column index (0..) to access
        :param value: value to set
        """
        ws = self.__ss.worksheet(sheet)
        assert axis in [0, 1], 'Wrong value for axis...'
        try:
            if axis == 0:
                col = ws.row_values(lookup_index + 1).index(lookup_value)
                row = value_index
            else:  # axis == 1
                row = ws.col_values(lookup_index + 1).index(lookup_value)
                col = value_index
        except ValueError:
            raise KeyError('Lookup value missing')
        ws.update_cell(row + 1, col + 1, value)

    def get_value_by_lookup(
            self,
            sheet: str,
            *,
            axis: int = 1,
            lookup_value: str,
            lookup_index: int,
            value_index: int,
    ):
        """
        Get a value based on vertical or horizontal lookup.
        :param sheet: worksheet name
        :param axis: vertical (1) or horizontal (0) lookup (default: 1)
        :param lookup_value: value to lookup
        :param lookup_index: row or column index (0..) to lookup in
        :param value_index: row or column index (0..) to access
        """
        ws = self.__ss.worksheet(sheet)
        assert axis in [0, 1], 'Wrong value for axis...'
        try:
            if axis == 0:
                col = ws.row_values(lookup_index + 1).index(lookup_value)
                row = value_index
            else:  # axis == 1
                row = ws.col_values(lookup_index + 1).index(lookup_value)
                col = value_index
        except ValueError:
            raise KeyError('Lookup value missing')
        return ws.cell(row + 1, col + 1)
