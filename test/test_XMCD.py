import pytest
import numpy as np
import hyperspy.io as hs
from align_panel.data_structure import ImageSetXMCD
from hyperspy._signals.signal2d import Signal2D


@pytest.fixture
def path1():
    return "data/92_pol+1_+23V_2ns.tiff"


@pytest.fixture
def path2():
    return "data/93_pol-1_+23V_2ns.tiff"


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


@pytest.mark.parametrize("path,result", [("path1", True), ("image1", False)])
def test_load(path, result, request):
    if result:
        imageset = ImageSetXMCD.load(request.getfixturevalue(path))
        assert isinstance(imageset.image, Signal2D)
    elif not result:
        with pytest.raises(ValueError):
            ImageSetXMCD.load(request.getfixturevalue(path))


@pytest.mark.parametrize(
    "image,result", [("image1", True), ("image2", True), ("path1", False)]
)
def test__init__(image, result, request):
    if result:
        imageset = ImageSetXMCD(request.getfixturevalue(image))
        assert isinstance(imageset.image, Signal2D)
    elif not result:
        with pytest.raises(TypeError):
            ImageSetXMCD(request.getfixturevalue(image))


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
    image_set_xmcd.flip_axes(axes="y")
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
