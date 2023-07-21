"""
Run from the test folder.
"""

import pytest
import numpy as np
import hyperspy.io as hs
from align_panel.data_structure import ImageSetXMCD
from hyperspy._signals.signal2d import Signal2D
import os


@pytest.fixture
def path1():
    return os.path.dirname(os.getcwd()) + "\data\92_pol+1_+23V_2ns.tiff"


@pytest.fixture
def path2():
    return os.path.dirname(os.getcwd()) + "\data\93_pol-1_+23V_2ns.tiff"


@pytest.fixture
def image1(path1):
    return hs.load(path1)


@pytest.fixture
def image2(path2):
    return hs.load(path2)


@pytest.fixture
def no_image():
    return None


@pytest.fixture
def image_set_xmcd(image1):
    return ImageSetXMCD(image1)


@pytest.fixture
def image_set_xmcd1(image2):
    return ImageSetXMCD(image2)


def test_load(path1):
    imageset = ImageSetXMCD.load(path1)
    assert isinstance(imageset.image, Signal2D)


def test_load_fail(image1):
    with pytest.raises(TypeError):
        ImageSetXMCD.load(image1)


def test__init__(image1):
    imageset = ImageSetXMCD(image1)
    assert isinstance(imageset.image, Signal2D)


def test__init__fail(path1):
    with pytest.raises(TypeError):
        ImageSetXMCD(path1)


def test_load_save(image_set_xmcd, tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    p = d / "test.nxs"
    image_set_xmcd.save(p)
    image_set_xmcd_load = ImageSetXMCD.load_from_nxs(p)
    assert image_set_xmcd.image == image_set_xmcd_load.image
    assert isinstance(image_set_xmcd_load.image, Signal2D)


def test_flip_axes(image_set_xmcd):
    original_image = image_set_xmcd.image.data
    image_set_xmcd.flip_axes(axis="y")
    assert image_set_xmcd.image.data.all() == np.flip(original_image, axis=0).all()


def test_set_axes(image_set_xmcd):
    image_set_xmcd.set_axes("x", "y", scale=0.01, units="nm")
    assert image_set_xmcd.image.axes_manager[0].scale == 0.01
    assert image_set_xmcd.image.axes_manager[0].units == "nm"
    assert image_set_xmcd.image.axes_manager[1].scale == 0.01
    assert image_set_xmcd.image.axes_manager[1].units == "nm"
    assert image_set_xmcd.image.axes_manager[0].name == "x"
    assert image_set_xmcd.image.axes_manager[1].name == "y"


def test_load_2_imagesets(image_set_xmcd, image_set_xmcd1, tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    p = d / "test.nxs"
    image_set_xmcd.save(p)
    image_set_xmcd1.save(p)
    image_set_xmcd_load = ImageSetXMCD.load_from_nxs(p, id_number=0)
    image_set_xmcd_load1 = ImageSetXMCD.load_from_nxs(p, id_number=1)
    assert image_set_xmcd.image == image_set_xmcd_load.image
    assert image_set_xmcd1.image == image_set_xmcd_load1.image
    assert isinstance(image_set_xmcd_load.image, Signal2D)
    assert isinstance(image_set_xmcd_load1.image, Signal2D)
