import logging
import os

import gribapi
import numpy as np
import numpy.ma as ma
import pytest

import gribtool as gt

logger = logging.getLogger("grib_tool")


def test_get_values(grib_name):
    with gt.GribSet(grib_name) as my_grib:
        msg = my_grib[0]
    assert isinstance(msg.get_values(), ma.MaskedArray)


# @pytest.mark.devel
# def test_set_values(grib_name):
#     with gt.GribSet(grib_name) as my_grib:
#         msg = my_grib[0]
#     values = msg.get_values()
#     values[:] = 0.0
#     msg.set_values(values)
#     gt.GribSet([msg]).save("test_set_values.grib")

#     with gt.GribSet("test_set_values.grib") as my_grib:
#         msg = my_grib[0]
#         assert np.all(msg.get_values() == 0.0)
#     os.remove("test_set_values.grib")

# @pytest.mark.devel
# def test_read_missing(grib_name):
#     import matplotlib.pyplot as plt
#     with gt.GribSet(grib_name) as my_grib:
#         Nx = grib_missing[0]["Ni"]
#         Ny = grib_missing[0]["Nj"]
#         missing = my_grib.filter(bitmapPresent=1)[0:1]
#         nomissing = my_grib.filter(bitmapPresent=0)[0:1]

#     missing.save("missing.grb")
#     nomissing.save("nomissing.grb")

#     v_missing = missing[0].get_values().reshape(Ny, Nx)
#     v_nomissing = nomissing[0].get_values().reshape(Ny, Nx)
#     v_newmissing = v_nomissing.copy()

#     # put missing values
#     values_newmissing.mask[:100,0:100] = True
#     grib_nomissing[0].set_values(values_newmissing)
#     grib_nomissing.save("newmissing.grb")

#     with gt.GribSet("newmissing.grb") as my_grib:
#         values = my_grib[0].get_values().reshape(Ny, Nx)
#         plt.imshow(values)
#         plt.show()


# plt.imshow(values_missing)
# plt.show()
# breakpoint()
# plt.imshow(values_nomissing)
# plt.show()
# breakpoint()
# plt.imshow(values_newmissing)
# plt.show()


# @pytest.mark.devel
def test_missing_values(grib_name):
    with gt.GribSet(grib_name) as my_grib:
        msg = my_grib[0]
    values = msg.get_values()
    msg["numberOfDataPoints"]
    msg["numberOfCodedValues"]
    msg["numberOfMissing"]
    # breakpoint()
    values[0:5000] = 9999
    msg["bitmapPresent"] = 1
    msg.set_values(values)
    gt.GribSet([msg]).save("missing_values.grib")
