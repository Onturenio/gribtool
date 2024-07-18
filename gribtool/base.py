import logging

import numpy as np
import numpy.ma as ma
from gribapi import (
    grib_clone,
    grib_get,
    grib_get_double,
    grib_get_string,
    grib_get_values,
    grib_keys_iterator_get_name,
    grib_keys_iterator_new,
    grib_keys_iterator_next,
    grib_new_from_file,
    grib_release,
    grib_set,
    grib_set_values,
    grib_write,
)
from gribapi.errors import KeyValueNotFoundError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print_keys = [
    "edition",
    "centre",
    "typeOfLevel",
    "level",
    "dataDate",
    "stepRange",
    "shortName",
    "packingType",
    "gridType",
]

print_keys = "ls"
# print_keys = "asdf"
# print_keys = "time"
# print_keys = "mars"


class _Registry:
    gribmessages = {}
    gribsets = {}

    @classmethod
    def register(cls, item):
        key = id(item)
        if isinstance(item, GribMessage):
            cls.gribmessages[key] = [item.gid]
        elif isinstance(item, GribSet):
            cls.gribsets[key] = [msg.gid for msg in item.messages]
        else:
            raise TypeError("Item must be GribMessage or GribSet instance")

    @classmethod
    def unregister(cls, item):
        key = id(item)
        if isinstance(item, GribMessage):
            if key in cls.gribmessages:
                del cls.gribmessages[key]
        elif isinstance(item, GribSet):
            del cls.gribsets[key]
        else:
            raise TypeError("Item must be GribMessage or GribSet instance")

    @classmethod
    def all_gids(cls):
        # list of all items NOT in the key
        gids = []
        for gids in cls.gribmessages.values():
            gids.extend(gids)
        for gids in cls.gribsets.values():
            gids.extend(gids)
        return set(gids)

    @classmethod
    def find_unique_gids(cls, element):
        """Find unique gids the elements of the register."""
        # join dictionaries
        dictionary = {**cls.gribmessages, **cls.gribsets}
        key = id(element)
        if len(dictionary) == 0:
            return []
        if len(dictionary) == 1:
            return dictionary[key]
        # list of all items NOT in the key
        others_items = [
            item for k, v in dictionary.items() if k != key for item in v
        ]

        # list of unique items in the key which are not in others_items
        unique_gids = [
            item for item in dictionary[key] if item not in others_items
        ]

        return unique_gids

    def __str__(self):
        return (
            f"Registry with {len(self.gribmessages)} GribMessages and"
            f" {len(self.gribsets)} GribSets]."
        )

    def __len__(self):
        return len(self.gribmessages) + len(self.gribsets)


class GribMessage:

    def __new__(cls, *args, **kwargs):
        """Prevent instantiation of GribMessage directly"""
        raise TypeError(
            "Cannot instantiate GribMessage directly. Clone from another"
            " GribMessage or slice a GribSet."
        )

    # def __init__(self, gid, no_registry=False, is_clone=False):
    #     self.gid = gid
    #     self.loaded = True
    #     if no_registry:
    #         return
    #     else:
    #         if is_clone:
    #             _Registry.register(self)
    #             return
    #         if gid not in _Registry.all_gids():
    #             # breakpoint()
    #             self.loaded = False
    #             raise TypeError(
    #                 "Message must be be previously loaded into memory"
    #                 " with a valid gid."
    #             )
    #         _Registry.register(self)

    def release(self):
        if hasattr(self, "loaded") and self.loaded:
            # logger.debug("Releasing GribMessage instance %s", id(self))
            grib_release(self.gid)
            _Registry.unregister(self)
            self.loaded = False

    def __getitem__(self, key):
        try:
            if isinstance(key, tuple) and len(key) == 2:
                key, type_ = key
                return grib_get(self.gid, key, type_)
            else:
                return grib_get(self.gid, key)
        except KeyValueNotFoundError:
            raise KeyValueNotFoundError(
                f"Key '{key}' not found in GRIB message"
            )

    def __setitem__(self, key, value):
        grib_set(self.gid, key, value)

    def _get_keys(self, print_keys):
        return {key: self[key] for key in print_keys}

    def get_values(self):
        return ma.masked_values(
            grib_get_values(self.gid),
            grib_get_double(self.gid, "missingValue"),
            shrink=False,
        )

    def set_values(self, values):
        if np.any(values.mask):
            missing = grib_get(self.gid, "missingValue")
            values[values.mask] = missing
            grib_set_values(self.gid, values)
            grib_set(self.gid, "bitmapPresent", 1)

    def clone(self):
        gid = grib_clone(self.gid)
        msg = super().__new__(GribMessage)
        msg.gid = gid
        msg.loaded = True
        _Registry.register(msg)
        return msg

    def _get_keys_from_namespace(self, namespace):
        gid = self.gid
        iterid = grib_keys_iterator_new(gid, namespace)

        dict_ = {}
        while grib_keys_iterator_next(iterid):
            keyname = grib_keys_iterator_get_name(iterid)
            keyval = grib_get_string(gid, keyname)
            dict_[keyname] = keyval
        return dict_

    def __str__(self):
        # Get the keys to print
        if isinstance(print_keys, str):
            dict_ = self._get_keys_from_namespace(print_keys)
        elif isinstance(print_keys, list):
            dict_ = self._get_keys(print_keys)
        else:
            raise TypeError(
                "print_keys must be a list of keys or"
                " a string with a namespace"
            )
        keys = dict_.keys()

        # Calculate the width of each column as the maximum of the length of
        # the key and the length of the value
        width = {key: len(key) for key in keys}
        for key, value in dict_.items():
            width[key] = max(width[key], len(str(value)))

        # Format the headings
        heading_str = "  ".join(f"{key:>{width[key]}}" for key in keys)

        # Format the row
        data_str = "  ".join(
            f"{str(dict_[key]):>{width[key]}}" for key in keys
        )

        return heading_str + "\n" + data_str

    def __del__(self):
        self.release()


class GribSet:
    def __init__(self, init, headers_only=False):
        if isinstance(init, str):
            messages = self._load(filename=init, headers_only=headers_only)
        elif isinstance(init, list):
            messages = init
            for message in messages:
                if not isinstance(message, GribMessage):
                    raise TypeError(
                        "messages must be list of GribMessage instances"
                    )
        else:
            raise TypeError(
                "messages must be a string or a list of GribMessage instances"
            )
        self.messages = messages
        self.loaded = True
        _Registry.register(self)

    def _load(self, filename, headers_only):
        messages = []
        with open(filename, "rb") as f:
            while True:
                gid = grib_new_from_file(f, headers_only)
                if gid is None:
                    break
                msg = super().__new__(GribMessage)
                msg.gid = gid
                msg.loaded = True
                messages.append(msg)
        logger.debug(f"Found {len(messages)} messages in {filename}")
        return messages

    def save(self, filename):
        with open(filename, "wb") as f:
            for message in self.messages:
                grib_write(message.gid, f)

    def release(self):
        if hasattr(self, "messages") and len(self.messages) > 0:
            unique_gids = _Registry.find_unique_gids(self)
            logger.debug(
                f"Releasing GridFile instance {id(self)}"
                f" with {len(self)} messages"
                f" of which {len(unique_gids)} are unique,"
                f" therefore released."
            )
            messages_to_release = [
                msg for msg in self.messages if msg.gid in unique_gids
            ]
            # for i, msg in enumerate(messages_to_release):
            for msg in messages_to_release:
                if msg.loaded:
                    msg.release()
            self.messages = []
            self.loaded = False
            _Registry.unregister(self)

    def __getitem__(self, index):
        if isinstance(index, int):
            msg = self.messages[index]
            _Registry.register(msg)
            return msg
        elif isinstance(index, slice):
            messages = self.messages[index]
            gribset = self.__class__(messages)
            # gribset.loaded = True
            # gribset.messages = messages
            # self._registry.add_gribset(gribset)

            # self.__class__._registry[id(gribset)] = [
            #     msg.gid for msg in messages
            # ]
            return gribset
        elif isinstance(index, tuple):
            index, key = index
            if isinstance(index, slice):
                return [msg[key] for msg in self.messages[index]]
            else:
                return self.messages[index][key]
        else:
            raise TypeError(
                "Unsupported index type. Must be int or slice, or"
                " tuple with int or slice and key"
            )

    def __repr__(self):
        return f"<GribFile with {len(self)} messages>"

    def __iter__(self):
        return iter(self.messages)

    def __len__(self):
        return len(self.messages)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def __del__(self):
        # logger.debug("Deleting GridFile instance %s", id(self))
        self.release()

    def __add__(self, other):
        if not isinstance(other, GribSet):
            raise TypeError(
                "unsupported operand type(s) for +: 'GribSet' and "
                f"'{other.__class__.__name__}'"
            )
        return self.__class__(self.messages + other.messages)

    def __str__(self):
        # Get the keys to print from the first message
        if isinstance(print_keys, str):
            dict_ = self[0]._get_keys_from_namespace(print_keys)
        elif isinstance(print_keys, list):
            dict_ = self[0]._get_keys(print_keys)
        else:
            raise TypeError(
                "print_keys must be a list of keys "
                "or a string with a namespace"
            )
        keys = dict_.keys()

        # Calculate the width of each column as the maximum of
        # the length of the key and the length of the value for all messages
        width = {key: len(key) for key in keys}
        for msg in self.messages:
            dict_ = msg._get_keys(keys)
            for key, value in dict_.items():
                width[key] = max(width[key], len(str(value)))

        # Format the headings
        heading_str = "  ".join(f"{key:>{width[key]}}" for key in keys)

        # Format the rows
        data_str = ""
        for msg in self.messages:
            # breakpoint()
            dict_ = msg._get_keys(keys)
            data_str += "  ".join(
                f"{str(dict_[key]):>{width[key]}}" for key in keys
            )
            data_str += "\n"

        return heading_str + "\n" + data_str

    def filter(self, **key_values):
        messages = []
        for msg in self.messages:
            for key, value in key_values.items():
                if msg[key] != value:
                    break
            else:
                messages.append(msg)

        return self.__class__(messages)
