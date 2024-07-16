import pytest

import gribtool as gt

logger = gt.logging.getLogger(__name__)


@pytest.mark.devel
def test_getitem_messages_are_unique(grib_name):
    my_grib = gt.GribSet(grib_name)
    assert isinstance(my_grib[-1], gt.GribMessage)
    a = my_grib[0]
    b = my_grib[0]
    assert a is b
    assert isinstance(a, gt.GribMessage)
    assert len(gt._registry) == 3

def test_getitem_gribsets_are_not_unique(grib_name):
    my_grib = gt.GribSet(grib_name)
    c = my_grib[1:15]
    d = my_grib[1:15]
    assert isinstance(c, gt.GribSet)
    assert c is not d
    assert len(gt._registry) == 3


def test_getitem_slice(grib_name):
    my_grib = gt.GribSet(grib_name)
    assert isinstance(my_grib[2:10], gt.GribSet)
    assert len(my_grib[2:10]) == 8


def test_getitem_after_purge(grib_name):
    my_grib = gt.GribSet(grib_name)
    my_grib.release()
    assert len(my_grib) == 0
    assert my_grib.loaded == False
    with pytest.raises(IndexError):
        my_grib[0]


def test_slicing_registry(grib_name):
    my_grib = gt.GribSet(grib_name)
    my_grib[0:1]
    my_grib[0:2]
    my_grib[0:3]
    my_grib[0:4]
