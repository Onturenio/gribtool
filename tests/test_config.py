import pytest

import gribtool as gt
from gribtool.config import set_config


def test_config_class():
    config = gt.config.Config()
    assert config.namespace is None
    assert len(config.print_keys) == 9

    with pytest.raises(ValueError):
        config = gt.config.Config(
            namespace="test", print_keys=["centre", "shortName"]
        )

    config = gt.config.Config(print_keys=["centre", "shortName"])
    assert config.print_keys == ["centre", "shortName"]

    config = gt.config.Config(namespace="ls")
    assert config.namespace == "ls"


def test_set_config_print_keys():
    set_config(print_keys=["centre", "shortName"])
    assert gt.config.rcParams.print_keys == ["centre", "shortName"]


def test_set_config_namespace():
    gt.config.set_config(namespace="time")
    assert gt.config.rcParams.namespace == "time"
    gt.config.set_config(max_rows=3)
    assert gt.config.rcParams.max_rows == 3
    assert gt.config.rcParams.namespace == "time"


def test_print(grib_name):
    gt.config.reset_config()
    my_grib = gt.GribSet(grib_name)
    with my_grib[0:2] as tmp_grib:
        assert len(str(tmp_grib).split("\n")[0].split()) == 9
        set_config(print_keys=["centre", "shortName"])
        assert len(str(tmp_grib).split("\n")[0].split()) == 2
        set_config(namespace="time")
        assert len(str(tmp_grib).split("\n")[0].split()) == 9
        assert "stepRange" in str(tmp_grib).split("\n")[0].split()


@pytest.mark.devel
def test_print_max(grib_name):
    gt.config.reset_config()
    my_grib = gt.GribSet(grib_name)
    assert len(str(my_grib).split("\n")) == 364
    gt.config.rcParams.max_rows = 15
    assert len(str(my_grib).split("\n")) == 17


