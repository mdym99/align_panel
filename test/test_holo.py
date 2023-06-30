from pathlib import Path
import pytest
import numpy as np
from hyperspy._signals.hologram_image import HologramImage
from hyperspy._signals.complex_signal import ComplexSignal
from hyperspy._signals.signal2d import Signal2D
from align_panel.data_structure import ImageSetHolo


@pytest.mark.parametrize(
    "path,path_ref",
    [("path1", "path2"), ("path1", "no_image")],
)
def test_load(path, path_ref, request):
    imageset = ImageSetHolo.load(
        request.getfixturevalue(path), request.getfixturevalue(path_ref)
    )
    assert (
        isinstance(imageset.image, HologramImage)
        and isinstance(imageset.ref_image, HologramImage)
        and (imageset.image.data.shape == imageset.ref_image.data.shape)
        or not imageset.ref_image
    )


@pytest.mark.parametrize(
    "path,path_ref",
    [("path1", "path5"), ("path5", "path1")],
)
def test_load_fail(path, path_ref, request):
    with pytest.raises(ValueError):
        ImageSetHolo.load(
            request.getfixturevalue(path), request.getfixturevalue(path_ref)
        )


@pytest.mark.parametrize(
    "image,image_ref",
    [
        ("image1", "image2"),
        ("image1", "no_image"),
    ],
)
def test___init__(image, image_ref, request):
    imageset = ImageSetHolo(
        request.getfixturevalue(image), request.getfixturevalue(image_ref)
    )
    assert (
        isinstance(imageset.image, HologramImage)
        and isinstance(imageset.ref_image, HologramImage)
        and (imageset.image.data.shape == imageset.ref_image.data.shape)
        or not imageset.ref_image
    )


@pytest.mark.parametrize(
    "image,image_ref",
    [
        ("image1", "image5"),
        ("image5", "image1"),
    ],
)
def test___init__fail(image, image_ref, request):
    with pytest.raises(ValueError):
        ImageSetHolo(request.getfixturevalue(image), request.getfixturevalue(image_ref))


def test__init__path_type_error(path1, path2):
    with pytest.raises(TypeError):
        ImageSetHolo(path1, path2)


def test_set_axes(image_set):
    image_set.set_axes("x", "y", scale=0.01, units="nm")
    assert image_set.image.axes_manager[0].scale == 0.01
    assert image_set.image.axes_manager[0].units == "nm"
    assert image_set.image.axes_manager[1].scale == 0.01
    assert image_set.image.axes_manager[1].units == "nm"
    assert image_set.image.axes_manager[0].name == "x"
    assert image_set.image.axes_manager[1].name == "y"
    assert str(image_set.image.axes_manager) == str(image_set.ref_image.axes_manager)


def test_flip_axes(image_set):
    original_image = image_set.image.data
    original_ref_image = image_set.ref_image.data
    image_set.flip_axes(axis="y")
    assert image_set.image.data.all() == np.flip(original_image, axis=0).all()
    assert image_set.ref_image.data.all() == np.flip(original_ref_image, axis=0).all()


def test_phase_calculation(image_set, tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    p = d / "phase.jpg"
    image_set.phase_calculation(save_jpeg=True, path=p)
    unwrapped_phase = Path(p)
    assert isinstance(image_set.wave_image, ComplexSignal)
    assert isinstance(image_set.unwrapped_phase, Signal2D)
    assert unwrapped_phase.is_file()


def test_save_load(image_set, tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    p = d / "test.nxs"
    image_set.phase_calculation()
    image_set.save(path=p)
    image_set_loaded = ImageSetHolo.load_from_nxs(p)
    assert image_set.image.data.all() == image_set_loaded.image.data.all()
    assert image_set.ref_image.data.all() == image_set_loaded.ref_image.data.all()
    assert (
        image_set.image.axes_manager[0].scale
        == image_set_loaded.image.axes_manager[0].scale
    )
    assert (
        image_set.image.axes_manager[1].units
        == image_set_loaded.image.axes_manager[1].units
    )
    assert (
        image_set.image.metadata["General"]["title"]
        == image_set_loaded.image.metadata["General"]["title"]
    )
    assert (
        image_set.image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
            "sb_position"
        ]
        == image_set_loaded.image.metadata["Signal"]["Holography"][
            "Reconstruction_parameters"
        ]["sb_position"]
    )
    assert (
        image_set_loaded.image.metadata.as_dictionary()
        == image_set.image.metadata.as_dictionary()
    )


def test_save_load_only_1image(image_set_no_ref, tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    p = d / "test.nxs"
    image_set_no_ref.save(path=p)
    image_set_loaded = ImageSetHolo.load_from_nxs(p)
    assert image_set_no_ref.image.data.all() == image_set_loaded.image.data.all()
    assert (
        image_set_no_ref.image.axes_manager[0].scale
        == image_set_loaded.image.axes_manager[0].scale
    )
    assert (
        image_set_no_ref.image.axes_manager[0].scale
        == image_set_loaded.image.axes_manager[0].scale
    )
    assert (
        image_set_no_ref.image.axes_manager[1].units
        == image_set_loaded.image.axes_manager[1].units
    )
    assert (
        image_set_no_ref.image.metadata["General"]["title"]
        == image_set_loaded.image.metadata["General"]["title"]
    )


def test_save_load_2_imagesets_full(image_set, image_set1, tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    p = d / "test.nxs"
    image_set.save(path=p)
    image_set1.save(path=p)
    image_set_loaded = ImageSetHolo.load_from_nxs(p, id_number=0)
    image_set_loaded1 = ImageSetHolo.load_from_nxs(p, id_number=1)
    assert image_set.image.data.all() == image_set_loaded.image.data.all()
    assert image_set.ref_image.data.all() == image_set_loaded.ref_image.data.all()
    assert image_set1.image.data.all() == image_set_loaded1.image.data.all()
    assert image_set1.ref_image.data.all() == image_set_loaded1.ref_image.data.all()
    assert (
        image_set_loaded.image.metadata.as_dictionary()
        == image_set.image.metadata.as_dictionary()
    )
    assert (
        image_set_loaded1.image.metadata.as_dictionary()
        == image_set1.image.metadata.as_dictionary()
    )


def test_save_load_2_imagesets_1ref(image_set, image_set_no_ref, tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    p = d / "test.nxs"
    image_set.save(path=p)
    image_set_no_ref.save(path=p)
    image_set_loaded = ImageSetHolo.load_from_nxs(p, id_number=0)
    image_set_loaded1 = ImageSetHolo.load_from_nxs(p, id_number=1)
    assert image_set.image.data.all() == image_set_loaded.image.data.all()
    assert image_set.ref_image.data.all() == image_set_loaded.ref_image.data.all()
    assert image_set_no_ref.image.data.all() == image_set_loaded1.image.data.all()
    assert image_set.ref_image.data.all() == image_set_loaded1.ref_image.data.all()
    assert (
        image_set_loaded.image.metadata.as_dictionary()
        == image_set.image.metadata.as_dictionary()
    )
    assert (
        image_set_loaded1.ref_image.metadata.as_dictionary()
        == image_set.ref_image.metadata.as_dictionary()
    )


def test__repr__(image_set):
    assert (
        str(repr(image_set))
        == "holography imageset \n image file name: Hb-.dm3\n  shape: (200, 200) \n reference file name: Rb-.dm3 \n  shape: (200, 200) \n "
    )
