import json
from abc import ABC, abstractclassmethod, abstractmethod
import hyperspy.io as hs
import numpy as np
from nexusformat.nexus import NXdata, NXentry, NXfield, NXlink, nxopen
from hyperspy._signals.hologram_image import HologramImage, Signal2D


class ImageSet(ABC):
    def __init__(self, image, type_measurement: str = None):
        self.images = {"image": image}
        self.type_measurement = type_measurement

    @property
    def image(self):
        return self.images.get("image", None)

    def __repr__(self):  #  review
        return (
            f"{self.type_measurement} image set \n "
            f"image file name: {self.images['image'].metadata['General']['original_filename']}"
            f"\n  shape: {self.images['image'].data.shape} \n "
        )

    @abstractclassmethod
    def load(cls, path):
        if not isinstance(path, str):
            raise TypeError("The path must be a string.")
        image = hs.load(path)
        if not image.metadata["General"]["title"]:
            image.metadata["General"]["title"] = image.metadata["General"][
                "original_filename"
            ].split(".")[0]
        return cls(image)

    @staticmethod
    def show_content(path, scope="short"):
        with nxopen(path, "r") as opened_file:
            if scope == "full":
                print(opened_file.tree)
            elif scope == "short":
                print(f"Content of file : {path}")
                for entry in opened_file["raw_data"]:
                    print(
                        entry
                        + " : "
                        + opened_file["raw_data"][entry].attrs["type_measurement"]
                    )

    def _save_image(self, key, file, id_number):  # private method, changed
        image = self.images[key]
        file[f"raw_data/imageset_{id_number}/raw_images/{key}"] = NXfield(
            image.data,
            name=f"{key}",
            signal=f"{key}",
            interpretation=f"{key}",
        )
        if str(image.axes_manager[0].units) == "<undefined>":
            print(
                "The axes are not properly defined. Image is saved without axes information."
            )
        else:
            file[f"raw_data/imageset_{id_number}/raw_images/{key}"].attrs[
                "units"
            ] = image.axes_manager[0].units
            file[f"raw_data/imageset_{id_number}/raw_images/{key}"].attrs[
                "1_axe"
            ] = image.axes_manager[0].name
            file[f"raw_data/imageset_{id_number}/raw_images/{key}"].attrs[
                "2_axe"
            ] = image.axes_manager[1].name
            file[f"raw_data/imageset_{id_number}/raw_images/{key}"].attrs[
                "scale"
            ] = image.axes_manager[0].scale

        file[f"raw_data/imageset_{id_number}/metadata/{key}_metadata"] = NXfield(
            json.dumps(image.metadata.as_dictionary())
        )

        file[
            f"raw_data/imageset_{id_number}/metadata/{key}_original_metadata"
        ] = NXfield(json.dumps(image.original_metadata.as_dictionary()))

    @abstractmethod
    def save(self, path, key_in: str = "image", id_number=0):  # changed, working
        with nxopen(path, "a") as opened_file:
            if "raw_data" not in opened_file:
                id_number = 0
                opened_file["raw_data"] = NXentry()
            else:
                data_stored = [*opened_file["raw_data"]]
                id_number = len(data_stored)
                if (
                    opened_file[
                        f"raw_data/imageset_{id_number-1}/raw_images/image"
                    ].shape
                    != self.image.data.shape
                ):
                    print("The shape of the image is not the same as the previous one.")
            print(f"Image set is saved with id_number: {id_number}.")
            opened_file[f"raw_data/imageset_{id_number}"] = NXdata()
            opened_file[f"raw_data/imageset_{id_number}"].attrs[
                "type_measurement"
            ] = self.type_measurement
            opened_file[f"raw_data/imageset_{id_number}/raw_images"] = NXdata()
            opened_file[f"raw_data/imageset_{id_number}/metadata"] = NXdata()
            self._save_image(file=opened_file, key=key_in, id_number=id_number)
            return id_number

    @abstractclassmethod
    def load_from_nxs(cls, path, key="image", id_number=0):  # changed, working
        with nxopen(path, "r") as opened_file:
            image = opened_file[f"raw_data/imageset_{id_number}/raw_images/{key}"]
            metadata = json.loads(
                opened_file[
                    f"raw_data/imageset_{id_number}/metadata/{key}_metadata"
                ].nxdata
            )
            original_metadata = json.loads(
                opened_file[
                    f"raw_data/imageset_{id_number}/metadata/{key}_original_metadata"
                ].nxdata
            )
            full_image = Signal2D(
                image.data,
                metadata=metadata,
                original_metadata=original_metadata,
            )
            if "units" in image.attrs:
                full_image.axes_manager[0].name = image.attrs["1_axe"]
                full_image.axes_manager[1].name = image.attrs["2_axe"]
                full_image.axes_manager[0].units = image.attrs["units"]
                full_image.axes_manager[1].units = image.attrs["units"]
                full_image.axes_manager[0].scale = image.attrs["scale"]
                full_image.axes_manager[1].scale = image.attrs["scale"]
            if not full_image.metadata["General"]["title"]:
                full_image.metadata["General"]["title"] = full_image.metadata[
                    "General"
                ]["original_filename"].split(".")[0]
        return cls(full_image)

    @staticmethod
    def delete_imageset_from_file(path, id_number=0):  # no change
        with nxopen(path, "a") as opened_file:
            del opened_file[f"raw_data/imageset_{id_number}"]

    @staticmethod
    def add_notes(path_notes, path_file, id_number=0):  # no change
        with nxopen(path_file, "a") as opened_file:
            with open(path_notes, "r", encoding="UTF-8") as notes:
                name_of_file = path_notes.split("/")[-1].split(".")[0]
                opened_file[
                    f"raw_data/imageset_{id_number}/metadata/{name_of_file}"
                ] = NXfield(notes.read())

    def set_axes(self, axe1_name: str, axe2_name: str, units, scale=None):
        for image in self.images.values():
            if image is not None:
                image.axes_manager[0].name = axe1_name
                image.axes_manager[1].name = axe2_name
                image.axes_manager[0].units = units
                image.axes_manager[1].units = units
                if scale is not None:
                    image.axes_manager[0].scale = scale
                    image.axes_manager[1].scale = scale

    def flip_axes(self, axes="x"):
        for image in self.images.values():
            if image is not None:
                if axes == "y":
                    image.data = np.flip(image.data, axis=0)
                elif axes == "x":
                    image.data = np.flip(image.data, axis=1)
                elif axes == "both":
                    image.data = np.flip(image.data, axis=0)
                    image.data = np.flip(image.data, axis=1)


class ImageSetHolo(ImageSet):
    def __init__(self, image: HologramImage, ref_image: HologramImage = None):
        if not isinstance(image, HologramImage):
            raise TypeError(
                "The image must be of the type HologramImage. Use the .load() method."
            )
        if ref_image:
            if not isinstance(ref_image, HologramImage):
                raise TypeError(
                    "The reference image must be of the type HologramImage. Use the .load() method."
                )
            if image.data.shape != ref_image.data.shape:
                raise ValueError(
                    "The image and the reference image must have the same shape."
                )

        super().__init__(image, type_measurement="holography")
        self.images["ref_image"] = ref_image
        self.images["wave_image"] = None  # do you need to define it in __init__?
        self.images["unwrapped_phase"] = None  # do you need to define it in __init__?

    @property
    def ref_image(self):
        return self.images.get("ref_image", None)

    @property
    def wave_image(self):
        return self.images.get("wave_image", None)

    @property
    def unwrapped_phase(self):
        return self.images.get("unwrapped_phase", None)

    def __repr__(self):  # review
        if self.ref_image:
            return (
                super().__repr__()
                + f"reference file name: {self.images['ref_image'].metadata['General']['original_filename']}"
                f" \n  shape: {self.images['ref_image'].data.shape} \n "
            )
        return super().__repr__() + "no reference image is loaded \n "

    @classmethod
    def load(cls, path, path_ref=None):
        if not isinstance(path, str):
            raise TypeError("The path must be a string.")
        image = hs.load(path, signal_type="hologram")
        if path_ref:
            if not isinstance(path_ref, str):
                raise TypeError("The path must be a string.")
            ref_image = hs.load(path_ref, signal_type="hologram")
            return cls(image, ref_image)
        return cls(image)

    def save(self, path, key_in="im+ref", id_number=0):  # changed, working, review
        with nxopen(path, "a") as opened_file:
            if "raw_data" not in opened_file:
                id_number = 0
                opened_file["raw_data"] = NXentry()
            else:
                data_stored = [*opened_file["raw_data"]]
                id_number = len(data_stored)
                if (
                    opened_file[
                        f"raw_data/imageset_{id_number-1}/raw_images/image"
                    ].shape
                    != self.image.data.shape
                ):
                    print("The shape of the image is not the same as the previous one.")
            print(f"Image set is saved with id_number: {id_number}.")
            opened_file[f"raw_data/imageset_{id_number}"] = NXdata()
            opened_file[f"raw_data/imageset_{id_number}"].attrs[
                "type_measurement"
            ] = self.type_measurement
            opened_file[f"raw_data/imageset_{id_number}/raw_images"] = NXdata()
            opened_file[f"raw_data/imageset_{id_number}/metadata"] = NXdata()
            if key_in == "im+ref":
                super()._save_image(file=opened_file, key="image", id_number=id_number)
                if self.images["ref_image"]:
                    super()._save_image(
                        file=opened_file,
                        key="ref_image",
                        id_number=id_number,  # ask Matthiew about this
                    )
                elif not self.images["ref_image"] and id_number == 0:
                    print("No reference image is saved or already saved.")
                elif not self.images["ref_image"] and id_number > 0:
                    print("The link to the previous reference image is saved.")
                    opened_file[
                        f"raw_data/imageset_{id_number}/raw_images/ref_image"
                    ] = NXlink(f"raw_data/imageset_{id_number-1}/raw_images/ref_image")
                    opened_file[
                        f"raw_data/imageset_{id_number}/metadata/ref_image_metadata"
                    ] = NXlink(
                        f"raw_data/imageset_{id_number-1}/metadata/ref_image_metadata"
                    )
                    opened_file[
                        f"raw_data/imageset_{id_number}/metadata/ref_image_original_metadata"
                    ] = NXlink(
                        f"raw_data/imageset_{id_number-1}/metadata/ref_image_original_metadata"
                    )

    @classmethod
    def load_from_nxs(cls, path, id_number=0):  # changed, working, review
        with nxopen(path, "r") as opened_file:
            image = opened_file[f"raw_data/imageset_{id_number}/raw_images/image"]
            metadata = json.loads(
                opened_file[
                    f"raw_data/imageset_{id_number}/metadata/image_metadata"
                ].nxdata
            )
            original_metadata = json.loads(
                opened_file[
                    f"raw_data/imageset_{id_number}/metadata/image_original_metadata"
                ].nxdata
            )
            full_image = HologramImage(
                image.data,
                metadata=metadata,
                original_metadata=original_metadata,
            )
            if "units" in image.attrs:
                full_image.axes_manager[0].name = image.attrs["1_axe"]
                full_image.axes_manager[1].name = image.attrs["2_axe"]
                full_image.axes_manager[0].units = image.attrs["units"]
                full_image.axes_manager[1].units = image.attrs["units"]
                full_image.axes_manager[0].scale = image.attrs["scale"]
                full_image.axes_manager[1].scale = image.attrs["scale"]
            if "ref_image" in opened_file[f"raw_data/imageset_{id_number}/raw_images"]:
                ref_image = opened_file[
                    f"raw_data/imageset_{id_number}/raw_images/ref_image"
                ].nxdata
                ref_metadata = json.loads(
                    opened_file[
                        f"raw_data/imageset_{id_number}/metadata/ref_image_metadata"
                    ].nxdata
                )
                ref_original_metadata = json.loads(
                    opened_file[
                        f"raw_data/imageset_{id_number}/metadata/ref_image_original_metadata"
                    ].nxdata
                )
                full_ref_image = HologramImage(
                    ref_image.data,
                    metadata=ref_metadata,
                    original_metadata=ref_original_metadata,
                )
                full_ref_image.axes_manager = full_image.axes_manager
                return cls(full_image, full_ref_image)
            return cls(full_image)

    def phase_calculation(self, visualize=False, save_jpeg=False, path=None):
        sb_position = self.ref_image.estimate_sideband_position(
            ap_cb_radius=None, sb="upper"
        )
        sb_size = self.ref_image.estimate_sideband_size(sb_position)

        self.images["wave_image"] = self.image.reconstruct_phase(
            self.ref_image,
            sb_position=sb_position,
            sb_size=sb_size,
            output_shape=np.shape(self.image.data),
        )
        self.images["unwrapped_phase"] = self.wave_image.unwrapped_phase()
        self.image.metadata["Signal"]["Holography"] = self.wave_image.metadata[
            "Signal"
        ]["Holography"]
        self.image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
            "sb_position"
        ] = list(
            self.wave_image.metadata["Signal"]["Holography"][
                "Reconstruction_parameters"
            ]["sb_position"].data.astype("float")
        )
        self.image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
            "sb_size"
        ] = list(
            self.wave_image.metadata["Signal"]["Holography"][
                "Reconstruction_parameters"
            ]["sb_size"].data.astype("float")
        )
        self.image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
            "sb_smoothness"
        ] = list(
            self.wave_image.metadata["Signal"]["Holography"][
                "Reconstruction_parameters"
            ]["sb_smoothness"].data.astype("float")
        )
        if (
            self.wave_image.metadata["Signal"]["Holography"][
                "Reconstruction_parameters"
            ]["sb_units"]
            is not None
        ):
            self.image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
                "sb_units"
            ] = list(
                self.wave_image.metadata["Signal"]["Holography"][
                    "Reconstruction_parameters"
                ]["sb_units"].data.astype("float")
            )

        if visualize:
            self.images["unwrapped_phase"].plot()

        if save_jpeg:
            self.images["unwrapped_phase"].save(path)


class ImageSetXMCD(ImageSet):
    def __init__(self, image: Signal2D):
        if not isinstance(image, Signal2D):
            raise TypeError(
                "The image must be of the type Signal2D. Use the .load() method."
            )
        super().__init__(image, type_measurement="xmcd")

    @classmethod
    def load(cls, path):
        return super().load(path)

    def save(self, path, key_in="image", id_number=0):
        super().save(path, key_in, id_number)

    @classmethod
    def load_from_nxs(cls, path, key="image", id_number=0):
        return super().load_from_nxs(path, key, id_number)
