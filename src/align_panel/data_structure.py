import json
import hyperspy.io as hs
import numpy as np
from nexusformat.nexus import NXdata, NXentry, NXfield, NXlink, nxopen
from hyperspy._signals.hologram_image import HologramImage, Signal2D
from abc import ABC, abstractclassmethod

class ImageSet(ABC):
    def __init__(self, image: Signal2D, type_measurement: str):
        self.image = image
        self.type_measurement = type_measurement

    @abstractclassmethod
    def load(cls, path):
        image = hs.load(path)
        return cls(image)

    @staticmethod
    def show_content(path, scope="short"):
        with nxopen(path, "r") as opened_file:
            if scope == "full":
                print(opened_file.tree)
            elif scope == "short":
                print(opened_file["raw_data"].entries)

    def write_data(self, file, id_number):
        file[f"raw_data/imageset_{id_number}/raw_images/image"] = NXfield(
            self.image.data,
            name="image",
            units="pixesl",
            signal="image",
            interpretation="image",
        )
        file[f"raw_data/imageset_{id_number}/metadata/metadata"] = NXfield(
            json.dumps(self.image.metadata.as_dictionary())
        )

        file[
            f"raw_data/imageset_{id_number}/metadata/original_metadata"
        ] = NXfield(json.dumps(self.image.original_metadata.as_dictionary()))

    def save_image(self, path, id_number=0):
        with nxopen(path, "a") as opened_file:
            if id_number == 0:
                opened_file["raw_data"] = NXentry()
            opened_file[f"raw_data/imageset_{id_number}"] = NXdata()
            opened_file[f"raw_data/imageset_{id_number}"].attrs["type_measurement"] = self.type_measurement
            opened_file[
                f"raw_data/imageset_{id_number}/raw_images"
            ] = NXdata()
            opened_file[f"raw_data/imageset_{id_number}/metadata"] = NXdata()
            self.write_data(
                file=opened_file, id_number=id_number
            )

    def load_image(self, path, id_number=0, type_measurement="holography"):
        with nxopen(path, "r") as opened_file:
            image = opened_file[
                f"raw_data/{type_measurement}_{id_number}/raw_images/image"
            ]
            metadata = json.loads(
                opened_file[
                    f"raw_data/{type_measurement}_{id_number}/metadata/metadata"
                ].nxdata
            )
            original_metadata = json.loads(
                opened_file[
                    f"raw_data/{type_measurement}_{id_number}/metadata/original_metadata"
                ].nxdata
            )
            self.image = HologramImage(
                image.data,
                metadata=metadata,
                original_metadata=original_metadata,
            )

    @staticmethod
    def delete_ImageSet_from_file(path, id_number=0, type_measurement="holography"):
        with nxopen(path, "a") as opened_file:
            del opened_file[f"raw_data/{type_measurement}_{id_number}"]

    @staticmethod
    def add_notes(path_notes, path_file, id_number=0, type_measurement="holography"):
        with nxopen(path_file, "a") as opened_file:
            with open(path_notes, "r") as notes:
                opened_file[
                    f"raw_data/{type_measurement}_{id_number}/metadata/notes"
                ] = NXfield(notes.read())

class ImageSetHolo(ImageSet):
    def __init__(self, image: HologramImage, ref_image: HologramImage = None):
        super().__init__(image, type_measurement="holography")
        self.ref_image = ref_image
        wave_image = None

    @classmethod
    def load(cls, path_image, path_ref_image = None):
        image = hs.load(path_image, signal_type="hologram")
        if path_ref_image:
            ref_image = hs.load(path_ref_image, signal_type="hologram")
            return cls(image, ref_image)
        return cls(image)

    def write_ref_data(self, file, id_number):
        file[f"raw_data/imageset_{id_number}/raw_images/ref_image"] = NXfield(
            self.ref_image.data,
            name="ref_image",
            units="pixesl",
            signal="image",
            interpretation="image",
        )
        file[
            f"raw_data/imageset_{id_number}/metadata/ref_metadata"
        ] = NXfield(json.dumps(self.ref_image.metadata.as_dictionary()))
        file[
            f"raw_data/imageset_{id_number}/metadata/ref_original_metadata"
        ] = NXfield(json.dumps(self.ref_image.original_metadata.as_dictionary()))

    def save_ref_image(self, path, id_number=0):
        with nxopen(path, "a") as opened_file:
            self.write_ref_data(
                file=opened_file, id_number=id_number)

    def save_ImageSet(self, path):
        with nxopen(path, "a") as opened_file:
            if "raw_data" not in opened_file:
                id_number = 0
            else:
                data_stored = [*opened_file["raw_data"]]
                id_number = len(data_stored)
            print(id_number)
            self.save_image(
                path=path, id_number=id_number
            )
        if self.ref_image:
            self.save_ref_image(path=path, id_number=id_number)
        if not self.ref_image and id_number == 0:
            print("No reference image is saved or already saved.")
        elif not self.ref_image and id_number > 0:
            print("The link to the previous reference image is saved.")
            with nxopen(path, "a") as opened_file:
                opened_file[
                    f"raw_data/imageset_{id_number}/raw_images/ref_image"
                ] = NXlink(f"raw_data/holography_{id_number-1}/raw_images/ref_image")

                opened_file[
                    f"raw_data/imageset_{id_number}/metadata/ref_metadata"
                ] = NXlink(f"raw_data/holography_{id_number-1}/metadata/ref_metadata")
                opened_file[
                    f"raw_data/imageset_{id_number}/metadata/ref_original_metadata"
                ] = NXlink(
                    f"raw_data/holography_{id_number-1}/metadata/ref_original_metadata"
                )

    def load_ref_image(self, path, id_number=0):
        with nxopen(path, "a") as opened_file:
            image = opened_file[
                f"raw_data/holography_{id_number}/raw_images/ref_image"
            ].nxdata
            metadata = json.loads(
                opened_file[
                    f"raw_data/holography_{id_number}/metadata/ref_metadata"
                ].nxdata
            )
            original_metadata = json.loads(
                opened_file[
                    f"raw_data/holography_{id_number}/metadata/ref_original_metadata"
                ].nxdata
            )
            self.ref_image = HologramImage(
                image.data,
                metadata=metadata,
                original_metadata=original_metadata,
            )

    def load_ImageSet(self, path, id_number=0):
        self.load_image(path, id_number)
        self.load_ref_image(path, id_number)
    
    def phase_calculation(self, visualize = False, save_jpeg = False, name=None):
        
        sb_position = self.ref_image.estimate_sideband_position(ap_cb_radius=None,
                                            sb ='upper')
        sb_size = self.ref_image.estimate_sideband_size(sb_position)
        
        self.wave_image = self.image.reconstruct_phase(self.ref_image,
                                  sb_position=sb_position,
                                  sb_size=sb_size, output_shape=np.shape(self.image.data))
        unwrapped_phase = self.wave_image.unwrapped_phase()

        if visualize:
            unwrapped_phase.plot()

        if save_jpeg:
            unwrapped_phase.save(f"{name}.jpg")
    

class ImageSetXMCD(ImageSet):
    def __init__(self, image: Signal2D):
        super().__init__(image, type_measurement="xmcd")

    @classmethod
    def load(cls, path):
        return super().load(path)

    def save_ImageSet(self, path, id_number=0):
        with nxopen(path, "a") as opened_file:
            if "raw_data" not in opened_file:
                id_number = 0
            else:
                data_stored = [*opened_file["raw_data"]]
                id_number = len(data_stored)
            print(id_number)
        self.save_image(path=path, id_number=id_number)

    def load_ImageSet(self, path, id_number=0):
        self.load_image(path, id_number, type_measurement="xmcd")