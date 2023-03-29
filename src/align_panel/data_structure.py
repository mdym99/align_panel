import json
from ast import literal_eval
import hyperspy.io as hs
from nexusformat.nexus import NXdata, NXentry, NXfield, nxopen
from hyperspy.signals import HologramImage


class ImageSet:
    def __init__(self, image=None, ref_image=None, type_measurement=""):
        self.image = image
        self.ref_image = ref_image
        self.type_measurement = type_measurement

    def save(self, file_name):
        with nxopen(file_name, "a") as f:
            data_stored = [*f]
            id_number = len(data_stored)
            print(id_number)
            f[f"{self.type_measurement}_{id_number}"] = NXentry()
            f[f"{self.type_measurement}_{id_number}/raw_images"] = NXdata()
            f[f"{self.type_measurement}_{id_number}/raw_images"].set_default()
            f[f"{self.type_measurement}_{id_number}/metadata"] = NXdata()
            f[f"{self.type_measurement}_{id_number}/raw_images/image"] = NXfield(
                self.image.data,
                name="raw_image",
                units="pixesl",
                signal="image",
                interpretation="image",
            )
            if self.type_measurement == "holography":
                f[f"{self.type_measurement}_{id_number}/metadata/metadata"] = NXfield(
                    str(self.image.metadata.as_dictionary())
                )
                f[f"{self.type_measurement}_{id_number}/metadata/original_metadata"] = NXfield(
                    str(self.image.original_metadata.as_dictionary())
                )

            if self.type_measurement == "xmcd":
                f[f"{self.type_measurement}_{id_number}/metadata/metadata"] = NXfield(
                    str(self.image.metadata.as_dictionary())
                )

                f[f"{self.type_measurement}_{id_number}/metadata/original_metadata"] = NXfield(
                    json.dumps(self.image.original_metadata.as_dictionary())
                )

            if self.ref_image:
                f[f"{self.type_measurement}_{id_number}/raw_images/ref_image"] = NXfield(
                    self.ref_image.data, name="ref_image", units="pixesl"
                )
                f[f"{self.type_measurement}_{id_number}/metadata/ref_metadata"] = NXfield(
                    str(self.ref_image.metadata.as_dictionary())
                )
                f[f"{self.type_measurement}_{id_number}/metadata/ref_original_metadata"] = NXfield(
                    str(self.ref_image.original_metadata.as_dictionary())
                )

    def create_ImageSet(self, path1, path2=None):
        if self.type_measurement == "holography":
            self.image = hs.load(path1, signal_type="hologram")
            if path2:
                self.ref_image = hs.load(path2, signal_type="hologram")
        elif self.type_measurement == "xmcd":
            self.image = hs.load(path1)
            
    @staticmethod
    def show_content(path, scope = 'short'):
        with nxopen(path, "r") as f:
            if scope == 'full':
                print(f.tree)
            elif scope == 'short':
                print(f.entries)

    def load_ImageSet(self, path, id_number=0):
        with nxopen(path, "r") as f:
            image = f[f"{self.type_measurement}_{id_number}/raw_images/image"]

            inf = float("inf")
            if self.type_measurement == "holography":
                metadata = eval(str(f[f"{self.type_measurement}_{id_number}/metadata/metadata"]))
                original_metadata = eval(
                    str(f[f"{self.type_measurement}_{id_number}/metadata/original_metadata"])
                )
                ref_image = f[f"{self.type_measurement}_{id_number}/raw_images/ref_image"]
                ref_metadata = eval(
                    str(f[f"{self.type_measurement}_{id_number}/metadata/ref_metadata"])
                )
                ref_original_metadata = eval(
                    str(f[f"{self.type_measurement}_{id_number}/metadata/ref_original_metadata"])
                )

                self.ref_image = HologramImage(
                    ref_image.data,
                    metadata=ref_metadata,
                    original_metadata=ref_original_metadata,
                )

            elif self.type_measurement == "xmcd":
                metadata = literal_eval(
                    str(f[f"{self.type_measurement}_{id_number}/metadata/metadata"])
                )
                original_metadata = literal_eval(
                    str(f[f"{self.type_measurement}_{id_number}/metadata/original_metadata"])
                )
            self.image = HologramImage(
                image.data, metadata=metadata, original_metadata=original_metadata
            )

            print(f[f"{self.type_measurement}_{id_number}"].tree)
    