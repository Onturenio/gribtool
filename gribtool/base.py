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


class GribMessage:
    def __init__(self, gid):
        if not isinstance(gid, int):
            raise TypeError("gid must be an interger")
        self._handle = gid
        self.loaded = True

    def __del__(self):
        self.release()

    def release(self):
        if hasattr(self, "loaded") and self.loaded:
            # logger.debug("Releasing GribMessage instance %s", id(self))
            grib_release(self._handle)
            if id(self) in GribSet._registry:
                del GribSet._registry[id(self)]
            self.loaded = False

    def __getitem__(self, key):
        try:
            if isinstance(key, tuple) and len(key) == 2:
                key, type_ = key
                return grib_get(self._handle, key, type_)
            else:
                return grib_get(self._handle, key)
        except KeyValueNotFoundError:
            raise KeyValueNotFoundError(
                f"Key '{key}' not found in GRIB message"
            )

    def __setitem__(self, key, value):
        grib_set(self._handle, key, value)

    def _get_keys(self, print_keys):
        return {key: self[key] for key in print_keys}

    def get_values(self):
        return ma.masked_values(
            grib_get_values(self._handle),
            grib_get_double(self._handle, "missingValue"),
            shrink=False,
        )

    def set_values(self, values):
        if np.any(values.mask):
            missing = grib_get(self._handle, "missingValue")
            values[values.mask] = missing
            grib_set_values(self._handle, values)
            grib_set(self._handle, "bitmapPresent", 1)

    def clone(self):
        gid = grib_clone(self._handle)
        msg = GribMessage(gid)
        GribSet._registry[id(msg)] = [gid]
        return msg

    def _get_keys_from_namespace(self, namespace):
        gid = self._handle
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
    _registry = {}

    # def __new__(cls, *args, **kwargs):
    #     """Prevent instantiation of GribSet directly"""
    #     raise TypeError(
    #         "Cannot instantiate GribSet directly. Use" " GribSet.from_file."
    #     )

    @staticmethod
    def _find_unique_items(dictionary, key):
        """Find unique items in a list member of a dictionary.

        The dictionary is expected to have a list as a value for the key. This
        function will return a set of unique items in the list given the
        key.
        """
        if len(dictionary) == 0:
            return []
        if len(dictionary) == 1:
            return dictionary[key]
        # list of all items NOT in the key
        others_items = [
            item for k, v in dictionary.items() if k != key for item in v
        ]

        # list of unique items in the key which are not in others_items
        key_items = [
            item for item in dictionary[key] if item not in others_items
        ]

        return key_items

    def __init__(self, init, headers_only=False):
        # Open a GRIB file and return a GribSet instance."""
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
            self._registry[id(self)] = [
                message._handle for message in messages
            ]
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

        # register the messages in the _registry dictionary
        self.__class__._registry[id(self)] = [
            message._handle for message in messages
        ]

    def save(self, filename):
        with open(filename, "wb") as f:
            for message in self.messages:
                grib_write(message._handle, f)

    def release(self):
        if hasattr(self, "messages") and len(self.messages) > 0:
            unique_messages = self._find_unique_items(self._registry, id(self))
            logger.debug(
                f"Releasing GridFile instance {id(self)}"
                f" with {len(self)} messages"
                f" of which {len(unique_messages)} are unique,"
                f" therefore released."
            )
            messages_to_release = [
                msg for msg in self.messages if msg._handle in unique_messages
            ]
            # breakpoint()
            for i, msg in enumerate(messages_to_release):
                if msg.loaded:
                    msg.release()
                    pass
            self.messages = []
            self.loaded = False
            del self._registry[id(self)]
            # breakpoint()

    def __getitem__(self, index):
        if isinstance(index, int):
            msg = self.messages[index]
            self._registry[id(msg)] = [msg._handle]
            return msg
        elif isinstance(index, slice):
            messages = self.messages[index]
            gribset = super().__new__(GribSet)
            gribset.loaded = True
            gribset.messages = messages

            self.__class__._registry[id(gribset)] = [
                msg._handle for msg in messages
            ]
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
