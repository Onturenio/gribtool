import pytest

import gribtool as gt

logger = gt.logging.getLogger("grib_tool")


def test_GribMessage_getitem(grib_name):
    my_grib = gt.GribSet(grib_name)
    message = my_grib[0]
    assert message["shortName", str] == "t"
    assert message["indicatorOfParameter", int] == 11
    assert message["indicatorOfParameter", str] == "t"
    assert message["level"] == 0
    assert message["indicatorOfTypeOfLevel"] == "sfc"


@pytest.mark.devel
def test_GribSet_gettitems(grib_name):
    my_grib = gt.GribSet(grib_name)
    assert isinstance(my_grib[0], gt.GribMessage)
    assert isinstance(my_grib[0:1], gt.GribSet)
    assert my_grib[0, "shortName"] == "t"
    assert my_grib[0:2, "shortName"] == ["t", "z"]


@pytest.mark.devel
def test_GribSet_gettitems_fail(grib_name):
    my_grib = gt.GribSet(grib_name)
    with pytest.raises(IndexError):
        my_grib[1000]
    with pytest.raises(TypeError):
        my_grib["shortName"]
