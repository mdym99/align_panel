import pickle
import hyperspy.io as hs
from nexusformat.nexus import NXdata, NXentry, NXfield, NXlink, nxopen
from hyperspy._signals.hologram_image import HologramImage


class ImageSet:
    def __init__(self, image=None):
        self.image = image

    def create_image(self, path, type_measurement="holography"):
        if type_measurement == "holography":
            self.image = hs.load(path, signal_type="hologram")
        elif type_measurement == "xmcd":
            self.image = hs.load(path)

    @staticmethod
    def show_content(path, scope="short"):
        with nxopen(path, "r") as opened_file:
            if scope == "full":
                print(opened_file.tree)
            elif scope == "short":
                print(opened_file["raw_data"].entries)

    def write_data(self, file, id_number, type_measurement):
        file[f"raw_data/{type_measurement}_{id_number}/raw_images/image"] = NXfield(
            self.image.data,
            name="image",
            units="pixesl",
            signal="image",
            interpretation="image",
        )
        file[f"raw_data/{type_measurement}_{id_number}/metadata/metadata"] = NXfield(
            str(pickle.dumps(self.image.metadata.as_dictionary()))
        )
        file[
            f"raw_data/{type_measurement}_{id_number}/metadata/original_metadata"
        ] = NXfield(str(pickle.dumps(self.image.original_metadata.as_dictionary())))

    def save_image(self, path, id_number=0, type_measurement="holography"):
        with nxopen(path, "a") as opened_file:
            if id_number == 0:
                opened_file["raw_data"] = NXentry()
            opened_file[f"raw_data/{type_measurement}_{id_number}"] = NXdata()
            opened_file[
                f"raw_data/{type_measurement}_{id_number}/raw_images"
            ] = NXdata()
            opened_file[f"raw_data/{type_measurement}_{id_number}/metadata"] = NXdata()
            self.write_data(
                file=opened_file, id_number=id_number, type_measurement=type_measurement
            )


class ImageSetHolo(ImageSet):
    def __init__(self, image=None, ref_image=None):
        super().__init__(image)
        self.ref_image = ref_image

    def create_ref_image(self, path):
        self.ref_image = hs.load(path, signal_type="hologram")

    def create_ImageSet(self, path_image, path_ref_image=None):
        self.create_image(path_image)
        if path_ref_image:
            self.create_ref_image(path_ref_image)

    def write_ref_data(self, file, id_number, type_measurement):
        file[f"raw_data/{type_measurement}_{id_number}/raw_images/ref_image"] = NXfield(
            self.ref_image.data,
            name="ref_image",
            units="pixesl",
            signal="image",
            interpretation="image",
        )
        file[
            f"raw_data/{type_measurement}_{id_number}/metadata/ref_metadata"
        ] = NXfield(str(pickle.dumps(self.ref_image.metadata.as_dictionary())))
        file[
            f"raw_data/{type_measurement}_{id_number}/metadata/ref_original_metadata"
        ] = NXfield(str(pickle.dumps(self.ref_image.original_metadata.as_dictionary())))

    def save_ref_image(self, path, id_number=0):
        with nxopen(path, "a") as opened_file:
            self.write_ref_data(
                file=opened_file, id_number=id_number, type_measurement="holography"
            )

    def save_ImageSet(self, path):
        with nxopen(path, "a") as opened_file:
            if "raw_data" not in opened_file:
                id_number = 0
            else:
                data_stored = [*opened_file["raw_data"]]
                id_number = len(data_stored)
            print(id_number)
            self.save_image(
                path=path, id_number=id_number, type_measurement="holography"
            )
        if self.ref_image:
            self.save_ref_image(path=path, id_number=id_number)
        if not self.ref_image and id_number == 0:
            print("No reference image is saved or already saved.")
        elif not self.ref_image and id_number > 0:
            with nxopen(path, "a") as opened_file:
                opened_file[
                    f"/raw_data/holography_{id_number}/raw_images/ref_image"
                ] = NXlink(f"/raw_data/holography_{id_number-1}/raw_images/ref_image")

                opened_file[
                    f"/raw_data/holography_{id_number}/metadata/ref_metadata"
                ] = NXlink(f"/raw_data/holography_{id_number-1}/metadata/ref_metadata")

                opened_file[
                    f"/raw_data/holography_{id_number}/metadata/ref_original_metadata"
                ] = NXlink(
                    f"/raw_data/holography_{id_number-1}/metadata/ref_original_metadata"
                )


class ImageSetXMCD(ImageSet):
    def create_ImageSet(self, path_image):
        self.create_image(path_image, type_measurement="xmcd")

    def save_ImageSet(self, path, id_number=0):
        with nxopen(path, "a") as opened_file:
            if "raw_data" not in opened_file:
                id_number = 0
            else:
                data_stored = [*opened_file["raw_data"]]
                id_number = len(data_stored)
            print(id_number)
        self.save_image(path=path, id_number=id_number, type_measurement="xmcd")