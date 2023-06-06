"""
Tests for reading terra15 format, version 5.
"""
import numpy as np
import pytest

import dascore as dc
from dascore.constants import REQUIRED_DAS_ATTRS
from dascore.core.schema import PatchFileSummary
from dascore.io.terra15.core import Terra15FormatterV6


@pytest.fixture(scope="class")
def terra15_v6_patch(terra15_v6_path):
    """Read the terra15 v5 file."""
    patch = dc.read(terra15_v6_path)[0]
    return patch


class TestReadTerra15V6:
    """Tests for reading the terra15 format."""

    def test_type(self, terra15_v6_patch):
        """Ensure the expected type is returned."""
        assert isinstance(terra15_v6_patch, dc.Patch)

    def test_attributes(self, terra15_v6_patch):
        """Ensure a few of the expected attrs exist in array."""
        attrs = dict(terra15_v6_patch.attrs)
        expected_attrs = {"time_min", "time_max", "distance_min", "data_units"}
        assert set(expected_attrs).issubset(set(attrs))

    def test_has_required_attrs(self, terra15_v6_patch):
        """ "Ensure the required das attrs are found"""
        assert set(REQUIRED_DAS_ATTRS).issubset(set(dict(terra15_v6_patch.attrs)))

    def test_coord_attr_time_equal(self, terra15_v6_patch):
        """The time reported in the attrs and coords should match"""
        attr_time = terra15_v6_patch.attrs["time_max"]
        coord_time = terra15_v6_patch.coords["time"].max()
        assert attr_time == coord_time

    def test_read_with_limits(self, terra15_v6_patch, terra15_v6_path):
        """If start/end time sare select the same patch ought to be returned."""
        attrs = terra15_v6_patch.attrs
        time = (attrs["time_min"], attrs["time_max"])
        dist = (attrs["distance_min"], attrs["distance_max"])
        patch = Terra15FormatterV6().read(
            terra15_v6_path,
            time=time,
            distance=dist,
        )[0]
        assert attrs["time_max"] == patch.attrs["time_max"]

    def test_time_dist_slice(self, terra15_v6_patch, terra15_v6_path):
        """Ensure slicing distance and time works from read func."""
        time_array = terra15_v6_patch.coords["time"]
        dist_array = terra15_v6_patch.coords["distance"]
        t1, t2 = time_array[10], time_array[40]
        d1, d2 = dist_array[10], dist_array[40]
        patch = Terra15FormatterV6().read(
            terra15_v6_path, time=(t1, t2), distance=(d1, d2)
        )[0]
        attrs, coords = patch.attrs, patch.coords
        assert attrs["time_min"] == coords["time"].min() == t1
        assert attrs["time_max"] == coords["time"].max()
        # since we use floats sometimes this are a little off.
        assert (attrs["time_max"] - t2) < (attrs["d_time"] / 4)
        assert attrs["distance_min"] == coords["distance"].min() == d1
        assert attrs["distance_max"] == coords["distance"].max() == d2

    def test_no_arrays_in_attrs(self, terra15_das_patch):
        """
        Ensure that the attributes are not arrays.
        Originally, attrs like time_min can be arrays with empty shapes.
        """
        for key, val in terra15_das_patch.attrs.items():
            assert not isinstance(val, np.ndarray)


class TestIsTerra15V6:
    """Tests for function to determine if a file is a terra15 file."""

    def test_format_and_version(self, terra15_v6_path):
        """Ensure version"""
        name, version = Terra15FormatterV6().get_format(terra15_v6_path)
        assert (name, version) == (Terra15FormatterV6.name, Terra15FormatterV6.version)

    def test_not_terra15_not_hdf5(self, dummy_text_file):
        """Test for not even a hdf5 file."""
        parser = Terra15FormatterV6()
        assert not parser.get_format(dummy_text_file)
        assert not parser.get_format(dummy_text_file.parent)

    def test_hdf5file_not_terra15(self, generic_hdf5):
        """Assert that the generic hdf5 file is not a terra15."""
        parser = Terra15FormatterV6()
        assert not parser.get_format(generic_hdf5)


class TestScanTerra15V6:
    """Tests for scanning terra15 file."""

    def test_basic_scan(self, terra15_v6_path):
        """Tests for getting summary info from terra15 data."""
        parser = Terra15FormatterV6()
        out = parser.scan(terra15_v6_path)
        assert isinstance(out, list)
        assert len(out) == 1
        assert isinstance(out[0], PatchFileSummary)

        data = out[0]
        assert data.file_format == parser.name
        assert data.file_version == parser.version