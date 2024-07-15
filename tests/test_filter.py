import pytest

import gribtool as gt

logger = gt.logging.getLogger("grib_tool")


@pytest.mark.devel
def test_filter(grib_name):
    with gt.GribSet(grib_name) as my_grib:
        my_filtered_grib = my_grib.filter(
            shortName="t",
        )
    assert all([msg["shortName"] == "t" for msg in my_filtered_grib])

    with gt.GribSet(grib_name) as my_grib:
        my_filtered_grib = my_grib.filter(
            level=925,
        )
    assert all([msg["level"] == 925 for msg in my_filtered_grib])

    from gribapi.errors import KeyValueNotFoundError
    with pytest.raises(KeyValueNotFoundError):
        with gt.GribSet(grib_name) as my_grib:
            my_filtered_grib = my_grib.filter(
                asdf=925,
            )
