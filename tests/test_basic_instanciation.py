import numpy.ma as ma
import pytest

import gribtool as gt

logger = gt.logging.getLogger("grib_tool")


def test_fail_on_instantiate_GribMessage():
    with pytest.raises(TypeError):
        gt.GribMessage("asdf")
    with pytest.raises(TypeError):
        gt.GribMessage()


@pytest.mark.devel
def test_release_GribMessage(grib_name):
    grib_file = gt.GribSet(grib_name)
    # breakpoint()
    grib_file.release()
    # msg = grib_file[0]
    # assert msg.loaded is True
    # msg.release()
    # assert msg.loaded is False
    # assert msg.release() is None
    # breakpoint()


def test_registry_GribMessage(grib_name):
    grib_file = gt.GribSet(grib_name)
    assert len(gt.GribSet._registry) == 1
    msg = grib_file[0]
    assert len(gt.GribSet._registry) == 2
    msg2 = msg.clone()
    assert len(gt.GribSet._registry) == 3
    grib_file.release()
    assert len(gt.GribSet._registry) == 2
    msg.release()
    assert len(gt.GribSet._registry) == 1
    msg2.release()
    assert len(gt.GribSet._registry) == 0


def test_clone_GribMessage(grib_name):
    grib_file = gt.GribSet(grib_name)
    assert len(gt.GribSet._registry) == 1
    msg = grib_file[0]
    grib_file.release()
    assert len(gt.GribSet._registry) == 1
    new_msg = msg.clone()
    assert len(gt.GribSet._registry) == 2
    assert isinstance(new_msg, gt.GribMessage)
    assert new_msg is not msg
    assert new_msg._handle != msg._handle
    assert new_msg["shortName"] == msg["shortName"]
    assert ma.all(new_msg.get_values() == msg.get_values())


def test_fail_on_instantiate_GribSet():
    with pytest.raises(TypeError):
        gt.GribSet()


def test_open_from_file(grib_name):
    grib_file = gt.GribSet(grib_name)
    assert hasattr(grib_file, "messages")
    assert hasattr(grib_file, "loaded")
    assert len(grib_file) == 362
    assert grib_file.loaded == True


def test_fail_open_from_file():
    with pytest.raises(FileNotFoundError):
        gt.GribSet("not_a_file")


def test_release(grib_name):
    grib_file = gt.GribSet(grib_name)
    assert len(gt.GribSet._registry) == 1
    grib_file.release()
    assert len(gt.GribSet._registry) == 0
    assert len(grib_file) == 0
    assert grib_file.loaded == False
    assert grib_file.release() == None
    grib_file.release()
