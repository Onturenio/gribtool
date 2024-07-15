import pytest

import gribtool as gt

logger = gt.logging.getLogger(__name__)


def test_iter(grib_name):
    my_grib = gt.GribSet(grib_name)
    for message in my_grib:
        assert isinstance(message, gt.GribMessage)


def test_context_manager(grib_name):
    with gt.GribSet(grib_name) as my_grib:
        assert len(my_grib) == 362
    assert my_grib.loaded == False


def test_sum(grib_name):
    my_grib = gt.GribSet(grib_name)
    my_grib2 = my_grib[2:10] + my_grib[10:20]
    my_grib2.save("test_sum.grb")
    with gt.GribSet("test_sum.grb") as my_grib3:
        assert len(my_grib3) == 18


def test_sum_fail(grib_name):
    my_grib = gt.GribSet(grib_name)
    with pytest.raises(TypeError):
        my_grib + "not a gribset"

@pytest.mark.devel
def test_print(grib_name):
    my_grib = gt.GribSet(grib_name)
    print(my_grib[0])
    print(my_grib[0:5])
    assert True
