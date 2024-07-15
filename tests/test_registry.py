import pytest

import gribtool as gt

logger = gt.logging.getLogger("grib_tool")


def test_registry(grib_name):
    my_grib1 = gt.GribSet(grib_name)
    assert len(my_grib1._registry) == 1
    my_grib2 = gt.GribSet(grib_name)
    assert len(my_grib1._registry) == 2

    assert id(my_grib1) in my_grib1._registry.gribsets
    assert id(my_grib2) in my_grib1._registry.gribsets

    # assert my_grib1._registry[id(my_grib1)] == [
    #     message._handle for message in my_grib1
    # ]
    my_grib1.release()
    assert my_grib1.messages == []
    # assert id(my_grib1) not in my_grib1._registry
    assert len(my_grib1._registry) == 1

@pytest.mark.devel
def test_relese_messages(grib_name):
    with gt.GribSet(grib_name) as my_grib1:
        my_grib2 = my_grib1[:10]
        my_grib3 = my_grib1[5:15]

    my_grib2.release()
    my_grib3.release()

