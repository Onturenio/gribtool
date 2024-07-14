import pytest

import gribtool as gt

logger = gt.logging.getLogger("grib_tool")


@pytest.fixture
def grib_name():
    return "./tests/mbr001_fc2024061800+024.grb1"

