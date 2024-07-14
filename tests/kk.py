import pytest

import grib_tool as gt

logger = gt.logging.getLogger("grib_tool")


@pytest.fixture
def grib_name():
    return "../GRIBS/mbr001/mbr001_fc2024061800+003.grb1"


def test_fail_on_instantiate():
    with pytest.raises(TypeError):
        gt.GribSet()


def test_open_from_file(grib_name):
    grib_file = gt.GribSet.from_file(grib_name)
    assert hasattr(grib_file, "messages")
    assert hasattr(grib_file, "loaded")
    assert len(grib_file) == 348
    assert grib_file.loaded == True


def test_fail_open_from_file():
    with pytest.raises(FileNotFoundError):
        gt.GribSet.from_file("not_a_file")


def test_open_from_messages(grib_name):
    my_grib = gt.GribSet.from_file(grib_name)
    messages = my_grib.messages
    # my_grib.purge()
    my_grib2 = gt.GribSet.from_messages(messages)
    assert len(my_grib2) == 348
    assert my_grib2.loaded == True
    assert len(my_grib2._registry) == 2
    my_grib.purge()
    assert len(my_grib2._registry) == 1
    my_grib2.purge()


def test_fail_open_from_messages():
    with pytest.raises(TypeError):
        gt.GribSet.from_messages("not a list")
    with pytest.raises(TypeError):
        gt.GribSet.from_messages([1, 2, 3])


def test_purge(grib_name):
    grib_file = gt.GribSet.from_file(grib_name)
    grib_file.purge()
    assert len(grib_file) == 0
    assert grib_file.loaded == False
    grib_file.purge()


def test_registry(grib_name):
    my_grib1 = gt.GribSet.from_file(grib_name)
    assert len(my_grib1._registry) == 1
    my_grib2 = gt.GribSet.from_file(grib_name)
    assert len(my_grib1._registry) == 2

    assert id(my_grib1) in my_grib1._registry
    assert id(my_grib2) in my_grib1._registry

    assert my_grib1._registry[id(my_grib1)] == [
        message._handle for message in my_grib1
    ]
    my_grib1.purge()
    assert my_grib1.messages == []
    assert id(my_grib1) not in my_grib1._registry
    assert len(my_grib1._registry) == 1


def test_iter(grib_name):
    my_grib = gt.GribSet.from_file(grib_name)
    for message in my_grib:
        assert isinstance(message, gt.GribMessage)
    my_grib.purge()


def test_getitem(grib_name):
    my_grib = gt.GribSet.from_file(grib_name)
    assert isinstance(my_grib[0], gt.GribMessage)
    assert isinstance(my_grib[-1], gt.GribMessage)


def test_getitem_slice(grib_name):
    my_grib = gt.GribSet.from_file(grib_name)
    assert isinstance(my_grib[2:10], gt.GribSet)
    assert len(my_grib[2:10]) == 8


def test_getitem_after_purge(grib_name):
    my_grib = gt.GribSet.from_file(grib_name)
    my_grib.purge()
    assert len(my_grib) == 0
    assert my_grib.loaded == False
    with pytest.raises(IndexError):
        my_grib[0]


def test_context_manager(grib_name):
    with gt.GribSet.from_file(grib_name) as my_grib:
        assert len(my_grib) == 348
    assert my_grib.loaded == False


def test_save_slice(grib_name):
    my_grib = gt.GribSet.from_file(grib_name)
    my_grib[2:10].save("test_save_slice.grb")
    my_grib2 = gt.GribSet.from_file("test_save_slice.grb")
    assert len(my_grib[2:10]) == len(my_grib2)


def test_print(grib_name):
    my_grib = gt.GribSet.from_file(grib_name)
    print(my_grib)
    del my_grib


def test_sum(grib_name):
    my_grib = gt.GribSet.from_file(grib_name)
    my_grib2 = my_grib[2:10] + my_grib[10:20]
    my_grib2.save("test_sum.grb")
    with gt.GribSet.from_file("test_sum.grb") as my_grib3:
        assert len(my_grib3) == 18


def test_sum_fail(grib_name):
    my_grib = gt.GribSet.from_file(grib_name)
    with pytest.raises(TypeError):
        my_grib + "not a gribset"


@pytest.mark.devel
def test_slice_then_purge(grib_name):
    with gt.GribSet.from_file(grib_name) as my_grib:
        logger.info(my_grib)
        my_subgrib = my_grib[0:10]

    assert len(my_subgrib._registry) == 1
    assert len(my_subgrib._registry[id(my_subgrib)]) == 10

    # logger.info(my_grib[0]["shortName"])
    # breakpoint()
    # del my_grib
    # logger.info(my_grib2)
    # logger.info(my_grib2[0])
    # logger.info(my_grib2[0]["shortName"])
    # handles = [message._handle for message in my_grib2]
    # logger.info(gt.grib_get(all_handles[0], "shortName"))
    # breakpoint()

    # logger.info("Handles: %s", handles)
    # logger.info("Saving...")
    # my_grib2.save("test_copy_del.grb")


def test_unique_gid():
    test_dict = {
        1: ["a", "b", "c", "d"],
        2: ["b", "e", "f", "g"],
        3: ["a", "h", "i", "j"],
    }
    unique_gid = gt.GribSet._find_unique_items(test_dict, 1)
    assert unique_gid == ["c", "d"]
    unique_gid = gt.GribSet._find_unique_items(test_dict, 2)
    assert unique_gid == ["e", "f", "g"]

    test_dict = {}
    assert gt.GribSet._find_unique_items(test_dict, 1) == []

    test_dict = {
        1: ["a", "b", "c", "d"],
    }
    assert gt.GribSet._find_unique_items(test_dict, 1) == ["a", "b", "c", "d"]


# def test_GribMessage_getitem():
#   my_grib = gt.open_grib('../GRIBS/mbr001/mbr001_fc2024061800+003.grb1')
#   message = my_grib[0]
#   assert message['shortName', str] == 't'
#   assert message['indicatorOfParameter', int] == 11
#   assert message['indicatorOfParameter', str] == 't'
#   assert message['level'] == 0
#   assert message['indicatorOfTypeOfLevel'] == 'sfc'
