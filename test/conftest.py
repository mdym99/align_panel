import hyperspy.io as hs
from hyperspy._signals.hologram_image import HologramImage
from align_panel.data_structure import ImageSetHolo
import pytest

# fixtures


@pytest.fixture(scope="session")
def path1():
    return "data/HoloSatNegative/Z1_H.dm4"


@pytest.fixture(scope="session")
def path2():
    return "data/HoloSatNegative/Z12_R.dm4"


@pytest.fixture(scope="session")
def path3():
    return "data/HoloSatPositive/Z1_H.dm4"


@pytest.fixture(scope="session")
def path4():
    return "data/HoloSatPositive/Z1et2_R.dm4"


@pytest.fixture(scope="session")
def path5():
    return "data/92_pol+1_+23V_2ns.tiff"


@pytest.fixture(scope="session")
def no_image():
    return None


@pytest.fixture(scope="session")
def image1(path1):
    image1 = hs.load(path1, signal_type="hologram")
    image1.crop("x", 0, 200)
    image1.crop("y", 0, 200)
    return image1


@pytest.fixture(scope="session")
def image2(path2):
    image2 = hs.load(path2, signal_type="hologram")
    image2.crop("x", 0, 200)
    image2.crop("y", 0, 200)
    return image2


@pytest.fixture(scope="session")
def image3(path3):
    image3 = hs.load(path3, signal_type="hologram")
    image3.crop("x", 0, 200)
    image3.crop("y", 0, 200)
    return image3


@pytest.fixture(scope="session")
def image4(path4):
    image4 = hs.load(path4, signal_type="hologram")
    image4.crop("x", 0, 200)
    image4.crop("y", 0, 200)
    return image4


@pytest.fixture(scope="session")
def image5(path5):
    return hs.load(path5, signal_type="hologram")


@pytest.fixture()
def image_set(image1, image2):
    return ImageSetHolo(image1, image2)


@pytest.fixture()
def image_set1(image3, image4):
    return ImageSetHolo(image3, image4)


@pytest.fixture()
def image_set_no_ref(image1):
    return ImageSetHolo(image1)
