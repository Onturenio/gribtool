import numpy.ma as ma
import pytest

import gribtool as gt
from gribtool.base import _Registry

logger = gt.logging.getLogger("grib_tool")


def test_fail_on_instantiate_GribMessage():
    with pytest.raises(TypeError):
        gt.GribMessage("asdf")
    with pytest.raises(TypeError):
        gt.GribMessage()
    with pytest.raises(TypeError):
        gt.GribMessage(1234)


def test_release_GribMessage(grib_name):
    grib_file = gt.GribSet(grib_name)
    msg = grib_file[0]
    grib_file.release()
    assert msg.loaded is True
    msg.release()
    assert msg.loaded is False
    assert msg.release() is None


def test_registry_GribMessage(grib_name):
    grib_file = gt.GribSet(grib_name)
    assert len(_Registry()) == 1
    assert len(_Registry.gribsets) == 1
    msg = grib_file[0]
    assert len(_Registry()) == 2
    assert len(_Registry.gribsets) == 1
    assert len(_Registry.gribmessages) == 1
    grib_file.release()
    assert len(_Registry()) == 1
    assert len(_Registry.gribsets) == 0
    assert len(_Registry.gribmessages) == 1
    msg.release()
    assert len(_Registry()) == 0
    assert len(_Registry.gribsets) == 0
    assert len(_Registry.gribmessages) == 0


def test_clone_GribMessage(grib_name):
    grib_file = gt.GribSet(grib_name)
    assert len(_Registry()) == 1
    msg = grib_file[0]
    grib_file.release()
    assert len(_Registry()) == 1
    assert len(_Registry.gribsets) == 0
    assert len(_Registry.gribmessages) == 1
    new_msg = msg.clone()
    assert isinstance(new_msg, gt.GribMessage)
    assert new_msg is not msg
    assert new_msg.gid != msg.gid
    assert new_msg["shortName"] == msg["shortName"]
    assert ma.all(new_msg.get_values() == msg.get_values())
    assert len(_Registry()) == 2
    assert len(_Registry.gribsets) == 0
    assert len(_Registry.gribmessages) == 2


def test_fail_on_instantiate_GribSet():
    with pytest.raises(TypeError):
        gt.GribSet()


def test_fail_open_from_file():
    with pytest.raises(FileNotFoundError):
        gt.GribSet("not_a_file")


def test_open_from_file(grib_name):
    grib_file = gt.GribSet(grib_name)
    assert hasattr(grib_file, "messages")
    assert hasattr(grib_file, "loaded")
    assert len(grib_file) == 362
    assert grib_file.loaded == True


@pytest.mark.devel
def test_open_from_GribMessages(grib_name):
    grib_file = gt.GribSet(grib_name)
    msg1 = grib_file[0]
    msg2 = grib_file[1]
    grib_file.release()
    assert len(_Registry()) == 2
    assert len(_Registry.gribsets) == 0
    assert len(_Registry.gribmessages) == 2
    assert _Registry.gribmessages[id(msg1)] == [msg1.gid]
    grib_file = gt.GribSet([msg1, msg2])
    assert len(grib_file) == 2
    assert (
        _Registry.gribmessages[id(msg1)][0]
        == _Registry().gribsets[id(grib_file)][0]
    )


def test_release(grib_name):
    grib_file = gt.GribSet(grib_name)
    assert len(_Registry()) == 1
    grib_file.release()
    assert len(_Registry()) == 0
    assert len(grib_file) == 0
    assert grib_file.loaded == False
    assert grib_file.release() == None
    grib_file.release()


def test_registry(grib_name):
    my_grib1 = gt.GribSet(grib_name)
    assert len(_Registry()) == 1
    my_grib2 = gt.GribSet(grib_name)
    assert len(_Registry()) == 2

    assert id(my_grib1) in _Registry.gribsets
    assert id(my_grib2) in _Registry.gribsets

    my_grib1.release()
    assert my_grib1.messages == []
    assert len(_Registry()) == 1


def test_relese_messages(grib_name):
    with gt.GribSet(grib_name) as my_grib1:
        my_grib2 = my_grib1[:10]
        my_grib3 = my_grib1[5:15]

    my_grib2.release()
    my_grib3.release()
