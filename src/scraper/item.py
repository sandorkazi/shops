import numpy as np
import pandas as pd
from collections import OrderedDict
from typing import List, Any


ItemSchema = OrderedDict(
    group=None,
    title=None,
    stock=None,
    converted_price=np.NaN,
    converted_old_price=np.NaN,
    discount=np.NaN,
    orig_price=np.NaN,
    orig_old_price=np.NaN,
    currency=None,
    conversion_rate=np.NaN,
    url=None,
    image_url=None,
)


class ColNames:
    raw = "_raw"
    error = "_error"
    etc = "_others"


ItemSchema[ColNames.raw] = None
ItemSchema[ColNames.error] = None


class ShopItem(OrderedDict):

    def __init__(
            self,
            **kwargs,
    ):
        super().__init__()
        for k, v in ItemSchema.items():
            super().__setitem__(k, kwargs.get(k, v))
        for k, v in kwargs.items():
            if k not in ItemSchema.keys():
                super().__setitem__(k, v)
        self._init_complete = True

    def __getattr__(
            self,
            name: str,
    ):
        try:
            return self.__getitem__(name)
        except KeyError:
            raise AttributeError(name)

    def __setattr__(
            self,
            key: str,
            value: Any,
    ):
        if "_init_complete" not in self.__dict__:
            return super().__setattr__(key, value)
        elif key in self.__dict__:
            super().__setattr__(key, value)
        else:
            self.__setitem__(key, value)

    def df(self):
        raise NotImplementedError()

    @staticmethod
    def empty_df():
        return pd.DataFrame(
            None,
            columns=list(ItemSchema.keys()) + [ColNames.error, ColNames.raw, ColNames.etc]
        )


class SingleShopItem(ShopItem):

    def df(self):
        s = pd.Series(
            index=ItemSchema.keys(),
            data=[getattr(self, k) for k in ItemSchema.keys()],
        )
        s[ColNames.etc] = {
            k: v
            for k, v in self.items()
            if k not in ItemSchema.keys()
        }
        return pd.DataFrame.from_records([s])


class CompositeShopItem(ShopItem):

    def _column(
            self,
            key: str,
            length: int,
    ) -> List:
        value = getattr(self, key)
        if isinstance(value, list):
            return value
        else:
            return [value for _ in range(length)]

    def df(self):
        lengths = [len(v) for v in self.values() if isinstance(v, list)]
        if lengths:
            try:
                assert min(lengths) == max(lengths), "Bad Shopitems as list length fluctuate."
                length = lengths[0]
                df = pd.DataFrame(
                    data=[self._column(k, length) for k in ItemSchema.keys()],
                    index=list(ItemSchema.keys()),
                    columns=range(length),
                )
                etc_keys = [k for k in self.keys() if k not in ItemSchema.keys()]
                dfx = pd.DataFrame(
                    data=[self._column(k, length) for k in etc_keys],
                    index=list(etc_keys),
                    columns=range(length),
                )
                # noinspection PyTypeChecker
                df2 = pd.DataFrame(
                    data=[dfx.apply(pd.Series.to_dict).values],
                    index=[ColNames.etc],
                    columns=df.columns,
                )
                return (
                    pd.concat([
                        df,
                        df2,
                    ])
                    .transpose()
                )
            except Exception as e:
                return pd.Series(
                    data={
                        ColNames.raw: self._raw,
                        ColNames.error: e,
                    }
                )
        else:
            s = pd.Series(
                index=ItemSchema.keys(),
                data=[getattr(self, k) for k in ItemSchema.keys()],
            )
            s[ColNames.etc] = {
                k: v
                for k, v in self.items()
                if k not in ItemSchema.keys()
            }
            return pd.DataFrame.from_records([s])
