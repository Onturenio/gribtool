class Config:
    def __init__(self, **kwargs):
        self.valid_options = ["print_keys", "namespace", "max_rows"]
        if "print_keys" in kwargs and "namespace" in kwargs:
            raise ValueError(
                "print_keys and namespace cannot be provided together"
            )
        default_print_keys = [
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
        self.namespace = kwargs.get("namespace", None)
        if kwargs.get("print_keys", None):
            self.print_keys = kwargs.pop("print_keys")
        else:
            self.print_keys = default_print_keys
        self.max_rows = kwargs.get("max_rows", None)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.valid_options:
                raise ValueError(f"Invalid option: {key}")
            setattr(self, key, value)

    def __repr__(self):
        return (f"Config(namespace={self.namespace},"
                f" print_keys={self.print_keys},"
                f" max_rows={self.max_rows})")


rcParams = Config()


def set_config(**kwargs):
    global rcParams
    rcParams.update(**kwargs)


def reset_config():
    global rcParams
    rcParams = Config()
