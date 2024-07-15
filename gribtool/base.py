import logging

import numpy as np
import numpy.ma as ma
from gribapi import *
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
    def __init__(self):
        self.gribmessages = {}
        self.gribsets = {}

    def add_gribset(self, gribset):
        key = id(gribset)
        self.gribsets[key] = [msg.gid for msg in gribset.messages]

    def remove_gribset(self, gribset):
        key = id(gribset)
        del self.gribsets[key]

    def add_gribmessage(self, gribmessage):
        key = id(gribmessage)
        self.gribmessages[key] = [gribmessage.gid]

    def remove_gribmessage(self, gribmessage):
        key = id(gribmessage)
        del self.gribmessages[key]

    def all_gids(self):
        # list of all items NOT in the key
        gids = []
        for (
            key,
            gids,
        ) in self.gribmessages.items():
            gids += gids
        for (
            key,
            gids,
        ) in self.gribsets.items():
            gids += gids
        return set(gids)

    def find_unique_gids(self, element):
        """Find unique gids the elements of the register"""
        # join dictionaries
        dictionary = {**self.gribmessages, **self.gribsets}
        key = id(element)
        if len(dictionary) == 0:
            return []
        if len(dictionary) == 1:
            return dictionary[key]
        # list of all items NOT in the key
        others_items = [
            item for k, v in dictionary.items() if k != key for item in v
        ]
        # breakpoint()

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


registry = _Registry()


class GribMessage:
    def __init__(self, gid, into_registry=False):
        if not isinstance(gid, int):
            raise TypeError("gid must be an interger")
        self.gid = gid
        self.loaded = True
        self._registry = registry
        if into_registry:
            self._registry.add_gribmessage(self)

    def __del__(self):
        self.release()

    def release(self):
        if hasattr(self, "loaded") and self.loaded:
            # logger.debug("Releasing GribMessage instance %s", id(self))
            grib_release(self.gid)
            if id(self) in self._registry.gribmessages:
                self._registry.remove_gribmessage(self)
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
        msg = GribMessage(gid)
        msg._registry.add_gribmessage(msg)
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
                "print_keys must be a list of keys or a string with a namespace"
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


class GribSet:
    def __init__(self, init, headers_only=False):
        # Open a GRIB file and return a GribSet instance."""
        self._registry = registry
        if isinstance(init, str):
            filename = init
            self._load(filename=filename, headers_only=headers_only)
        elif isinstance(init, list):
            messages = init
            for message in messages:
                if not isinstance(message, GribMessage):
                    raise TypeError(
                        "messages must be list of GribMessage instances"
                    )
            self.messages = messages
            self.loaded = True
            self._registry.add_gribset(self)
        else:
            raise TypeError("messages must be list of GribMessage instances")

    def _load(self, filename, headers_only):
        messages = []
        with open(filename, "rb") as f:
            n_messages = grib_count_in_file(f)
            logger.debug("Found %d messages in %s", n_messages, filename)
            for i in range(n_messages):
                gid = grib_new_from_file(f, headers_only)
                messages.append(GribMessage(gid))
        self.loaded = True
        self.messages = messages

        self._registry.add_gribset(self)

    def save(self, filename):
        with open(filename, "wb") as f:
            for message in self.messages:
                grib_write(message.gid, f)

    def release(self):
        if hasattr(self, "messages") and len(self.messages) > 0:
            unique_gids = self._registry.find_unique_gids(self)
            # breakpoint()
            logger.debug(
                f"Releasing GridFile instance {id(self)}"
                f" with {len(self)} messages"
                f" of which {len(unique_gids)} are unique,"
                f" therefore released."
            )
            messages_to_release = [
                msg for msg in self.messages if msg.gid in unique_gids
            ]
            for i, msg in enumerate(messages_to_release):
                if msg.loaded:
                    msg.release()
            self.messages = []
            self.loaded = False
            self._registry.remove_gribset(self)

    def __getitem__(self, index):
        if isinstance(index, int):
            msg = self.messages[index]
            self._registry.add_gribmessage(msg)
            return msg
        elif isinstance(index, slice):
            messages = self.messages[index]
            gribset = self.__class__(messages)
            gribset.loaded = True
            gribset.messages = messages
            self._registry.add_gribset(gribset)

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
                "print_keys must be a list of keys or a string with a namespace"
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
