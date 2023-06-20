"""
    This module contains classes that define the data structure of the imagesets.
    Saving and loading procedures are defined, the saved files are based on the NeXus format.
"""
import json
from abc import ABC, abstractclassmethod, abstractmethod
import hyperspy.io as hs
import numpy as np
from nexusformat.nexus import NXdata, NXentry, NXfield, NXlink, nxopen
from hyperspy._signals.hologram_image import HologramImage, Signal2D


class ImageSet(ABC):
    """
    An abstract parent class for the data structure of the imagesets.

    The child classes are ImageSetHolo and ImageSetXMCD.

    Attributes
    ----------
    images : dict
        A dictionary containing the images of the imageset. The keys are the names of the images.

    type_measurement : str
        The type of the measurement. It is used as an attribute of the NXdata group 
        in the NeXus file.

    Methods
    -------
    load(path)
        Loads the image from the path and returns an instance of ImageSet object.

    show_content(path, scope="short")
        Prints the content of the NeXus file. The scope can be "short" or "full".

    __save_image(key, file, id_number)
        Method to save the image inside the NeXus file. It is used by the save method.
        Key is the name of the image, file is the NeXus file and id_number is the order number 
        of the imageset.

    __file_prep(file)
        Method to prepare the NeXus file for saving of the imageset. It is used by the save method.
        File is the opened NeXus file, in which imageset is saved.

    save(path)
        Saves the imageset in the NeXus file. It utilizes the __save_image and __file_prep methods.
        Path is the path of the NeXus file, in which imageset is saved.

    __load_image_from_nxs(file, key, id_number)
        Method to load image from the NeXus file. It is used by the load_from_nxs method.
        File is the opened NeXus file, key is the name of the image and id_number is the order number 
        of the imageset.

    load_from_nxs(path, id_number=0)
        Loads the imageset from the NeXus file. It utilizes the __load_image_from_nxs method.
        Path is the path of the NeXus file and id_number is the order number of the imageset.

    delete_imageset_from_file(path, id_number=0)
        Deletes the imageset from the NeXus file.
        Path is the path of the NeXus file and id_number is the order number of the imageset.

    add_notes(path_notes, path_file, id_number=0)
        Adds notes to the NeXus file.
        Path_notes is the path of the file containing the notes, path_file is the path 
        of the NeXus file and id_number is the order number of the imageset.

    images_content()
        Generator that yields the images of the imageset, that are created.

    set_axes(axis1_name: str, axis2_name: str, units, scale=None)
        Sets the axes of all the images of the imageset.
        Axis1_name is the name of the first axis, axis2_name is the name of the second axis,
        units is the units of the axes and scale is the scale of the axes.

    flip_axes(axis="y")
        Flips the axes of all the images of the imageset.
        Axis is the axis to be flipped. It can be "x", "y" or "both".

    """

    def __init__(self, image, type_measurement: str = None):
        """
        Parameters
        ----------
        image :
            A hyperspy object containing the image and its metadata.

        type_measurement : str, optional
            Describes the type of measurement, by default None
        """
        self.images = {"image": image}  # named tuple could be better?
        self.type_measurement = type_measurement

    @property
    def image(self):
        """
        Property that returns the image of the imageset.

        Returns
        -------
        A hyperspy object containing the image and its metadata.

        """
        return self.images.get("image", None)

    def __repr__(self):
        return (
            f"{self.type_measurement} image set \n "
            f"image file name: {self.image.metadata['General']['original_filename']}"
            f"\n  shape: {self.image.data.shape} \n "
        )

    @abstractclassmethod
    def load(cls, path: str):
        """
        Class method that loads the image from the path and returns an instance of ImageSet object.

        Parameters
        ----------
        path : str
            Path of the image file.

        Returns
        -------
        An instance of ImageSet object containing the image and its metadata.
        The image is loaded with the help of the hyperspy library.

        Raises
        ------
        TypeError
            If the path is not a string, raise a TypeError.
        """
        if not isinstance(path, str):
            raise TypeError("The path must be a string.")
        image = hs.load(path)
        if not image.metadata["General"]["title"]:
            image.metadata["General"]["title"] = image.metadata["General"][
                "original_filename"
            ].split(".")[0]
        return cls(image)

    @staticmethod
    def show_content(path: str, scope="short"):
        """
        Method that prints the content of the NeXus file. The scope can be "short" or "full".

        Parameters
        ----------
        path : str
            Path of the NeXus file.
        scope : str, optional
           Defines the punctuality of the printed content, by default "short"

           Options:
            "short" prints only the names of the image sets and their types

            "full" prints the whole content of the NeXus file
        """
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

    def __save_image(
        self, key: str, file, id_number: int
    ):  # could be changed to be without __
        """
        Method that saves image inside the NeXus file. Image is saved into the raw_data group,
        metadata and original metadata are saved into the metadata group, axes are saved as
        attributes to image.
        It is used by the save method.

        Parameters
        ----------
        key : str
            Key of the image in the images dictionary.
        file : NXlinkgroup | NXgroup
            Opened NeXus file, in which the image is saved.
        id_number : int
            Number of the imageset. Defines the order of the imagesets in the NeXus file.
        """
        image = self.images[key]
        file[f"raw_data/imageset_{id_number}/raw_images/{key}"] = NXfield(
            image.data,
            name=f"{key}",
            signal=f"{key}",
            interpretation=f"{key}",
        )
        if (
            str(image.axes_manager[0].units) == "<undefined>"
        ):  # more uniform way is needed
            print(
                "The axes are not properly defined. Image is saved without axes information."
            )
        else:
            file[f"raw_data/imageset_{id_number}/raw_images/{key}"].attrs[
                "units"
            ] = image.axes_manager[0].units
            file[f"raw_data/imageset_{id_number}/raw_images/{key}"].attrs[
                "1_axis"
            ] = image.axes_manager[0].name
            file[f"raw_data/imageset_{id_number}/raw_images/{key}"].attrs[
                "2_axis"
            ] = image.axes_manager[1].name
            file[f"raw_data/imageset_{id_number}/raw_images/{key}"].attrs[
                "scale"
            ] = image.axes_manager[0].scale

        file[f"raw_data/imageset_{id_number}/metadata/{key}_metadata"] = NXfield(
            json.dumps(image.metadata.as_dictionary())
        )

        file[f"raw_data/imageset_{id_number}/metadata/{key}_original_metadata"] = NXfield(
            json.dumps(image.original_metadata.as_dictionary())
        )

    def __file_prep(self, file):
        """
        Method that prepares the NeXus file for saving the imageset. It is used by the save method.

        Parameters
        ----------
        file : NXlinkgroup | NXgroup
            Opened NeXus file, in which the image is saved.
        Returns
        -------
        id_number : int
            Number of the imageset. Defines the order of the imagesets in the NeXus file.
        """
        if "raw_data" not in file:
            id_number = 0
            file["raw_data"] = NXentry()
        else:
            data_stored = [*file["raw_data"]]
            id_number = len(data_stored)
            if (
                file[f"raw_data/imageset_{id_number-1}/raw_images/image"].shape
                != self.image.data.shape
            ):
                print("The shapes of the images are not the same with the previous ones.")
        print(f"Image set is saved with id_number: {id_number}.")
        file[f"raw_data/imageset_{id_number}"] = NXdata()
        file[f"raw_data/imageset_{id_number}"].attrs[
            "type_measurement"
        ] = self.type_measurement
        file[f"raw_data/imageset_{id_number}/raw_images"] = NXdata()
        file[f"raw_data/imageset_{id_number}/metadata"] = NXdata()
        return id_number

    @abstractmethod
    def save(self, path: str):
        """
        Method that saves the imageset in the NeXus file. It utilizes the __save_image
        and __file_prep methods.

        Parameters
        ----------
        path : str
            Path of the NeXus file, in which the imageset is saved.
        """
        with nxopen(path, "a") as opened_file:
            id_number = self.__file_prep(opened_file)
            self.__save_image(file=opened_file, key="image", id_number=id_number)

    @staticmethod
    def __load_image_from_nxs(file, key: str, id_number: int):
        """
        Method that loads the image from the NeXus file. It is used by the load_from_nxs method.

        Parameters
        ----------
        file : NXlinkgroup | NXgroup
            Opened NeXus file, in which the image is saved.
            The file is opened with function nxopen from nexusformat library.

        key : str
            Key of the image in the images dictionary.

        id_number : int
            Number of the imageset. Defines the order of the imagesets in the NeXus file.

        Returns
        -------
        full_image: Signal2D
            A hyperspy object containing the image and its metadata.
        """
        image = file[f"raw_data/imageset_{id_number}/raw_images/{key}"]
        metadata = json.loads(
            file[f"raw_data/imageset_{id_number}/metadata/{key}_metadata"].nxdata
        )
        original_metadata = json.loads(
            file[f"raw_data/imageset_{id_number}/metadata/{key}_original_metadata"].nxdata
        )
        full_image = Signal2D(
            image.data,
            metadata=metadata,
            original_metadata=original_metadata,
        )
        if "units" in image.attrs:
            full_image.axes_manager[0].name = image.attrs["1_axis"]
            full_image.axes_manager[1].name = image.attrs["2_axis"]
            full_image.axes_manager[0].units = image.attrs["units"]
            full_image.axes_manager[1].units = image.attrs["units"]
            full_image.axes_manager[0].scale = image.attrs["scale"]
            full_image.axes_manager[1].scale = image.attrs["scale"]
        if not full_image.metadata["General"]["title"]:
            full_image.metadata["General"]["title"] = full_image.metadata["General"][
                "original_filename"
            ].split(".")[0]
        return full_image

    @abstractclassmethod
    def load_from_nxs(cls, path: str, id_number: int = 0):
        """
        Abstract class method that loads the imageset from the NeXus file. It utilizes the
        __load_image_from_nxs method.
        Parameters
        ----------
        path : str
            Path of the NeXus file, from which the imageset is loaded.
        id_number : int, optional
        Number of the imageset. Defines the order of the imagesets in the NeXus file,
        by default 0

        Returns
        -------
        Instance of the ImageSet class.
        """
        with nxopen(path, "r") as opened_file:
            image = cls.__load_image_from_nxs(
                file=opened_file, key="image", id_number=id_number
            )
            return cls(image)

    @staticmethod
    def delete_imageset_from_file(path: str, id_number: int = 0):
        """
        Method that deletes the imageset from the NeXus file.

        Parameters
        ----------
        path : str
            Path of the NeXus file, from which the imageset is deleted.
        id_number : int, optional
            Number of the imageset. Defines the order of the imagesets in the NeXus file, 
            by default 0
        """
        with nxopen(path, "a") as opened_file:
            del opened_file[f"raw_data/imageset_{id_number}"]

    @staticmethod
    def add_notes(path_notes: str, path_file: str, id_number: int = 0):
        """
        Method that adds notes to the NeXus file.

        Parameters
        ----------
        path_notes : str
            Path of the file containing the notes.
        path_file : str
            Path of the NeXus file, to which the notes are added.
        id_number : int, optional
            Number of the imageset. Defines the order of the imagesets in the NeXus file, 
            by default 0
        """
        with nxopen(path_file, "a") as opened_file:
            with open(path_notes, "r", encoding="UTF-8") as notes:
                name_of_file = path_notes.split("/")[-1].split(".")[0]
                opened_file[
                    f"raw_data/imageset_{id_number}/metadata/{name_of_file}"
                ] = NXfield(notes.read())

    def images_content(self):
        """
        Generator that yields the images of the imageset.

        Yields
        ------
        image : Signal2D
            A hyperspy objects saved in the images dictionary.
        """
        for image in self.images.values():
            if image is not None:
                yield image

    def set_axes(self, axis1_name: str, axis2_name: str, units: str, scale: int = None):
        """
        Method that sets the axes of the images of the imageset.

        Parameters
        ----------
        axis1_name : str
            Name of the first axis.
        axis2_name : str
            Name of the second axis.
        units : str
            Units of the axes.
        scale : int, optional
            Scale of the axes, by default None
        """
        for image in self.images_content():
            image.axes_manager[0].name = axis1_name
            image.axes_manager[1].name = axis2_name
            image.axes_manager[0].units = units
            image.axes_manager[1].units = units
            if scale is not None:
                image.axes_manager[0].scale = scale
                image.axes_manager[1].scale = scale

    def flip_axes(self, axis="y"):
        """
        Method that flips the axes of the images of the imageset.

        Parameters
        ----------
        axis : str, optional
            Defines the axis, in which the image is flipped, by default "y"
        """
        for image in self.images_content():
            if axis == "y":
                image.data = np.flip(image.data, axis=0)
            elif axis == "x":
                image.data = np.flip(image.data, axis=1)
            elif axis == "both":
                image.data = np.flip(image.data, axis=0)
                image.data = np.flip(image.data, axis=1)


class ImageSetHolo(ImageSet):
    """
    A child class of the ImageSet class. It is used for the holography image sets.
    This class contains the methods for saving, loading and processing of the holography imagesets.
    Phase calculation is implemented.

    Parameters
    ----------
    images : dict
        Dictionary containing the images of the imageset. The keys are the names of the images.
        The keys are:
            image: HologramImage - the hologram image of a sample
            ref_image: HologramImage - the reference image 
            wave_image: ComplexSignal2D - the reconstructed wave image
            unwrapped_phase: Signal2D - the unwrapped phase image
    
    type_measurement : str 
        The type of the measurement. It is used as an attribute of the NXdata group.
        by default "holography"

    Methods
    -------

    """
    def __init__(self, image: HologramImage, ref_image: HologramImage = None, type_measurement: str = "holography"):
        """_summary_

        Parameters
        ----------
        image : HologramImage
            Hologram image of a sample.
        ref_image : HologramImage, optional
            Reference image, by default None
        type_measurement : str, optional
            Describes the type of measurement, by default "holography"

        Raises
        ------
        TypeError
            If the image or the reference image is not of the type HologramImage, raise a TypeError.
        ValueError
            If the image and the reference image do not have the same shape, raise a ValueError.
        """
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

        super().__init__(image, type_measurement = type_measurement)
        self.images["ref_image"] = ref_image
        self.images["wave_image"] = None  
        self.images["unwrapped_phase"] = None 

    @property
    def ref_image(self):
        return self.images.get("ref_image", None)

    @property
    def wave_image(self):
        return self.images.get("wave_image", None)

    @property
    def unwrapped_phase(self):
        return self.images.get("unwrapped_phase", None)

    def __repr__(self):
        if self.ref_image:
            return (
                super().__repr__()
                + f"reference file name: {self.ref_image.metadata['General']['original_filename']}"
                f" \n  shape: {self.ref_image.data.shape} \n "
            )
        return super().__repr__() + "no reference image is loaded \n "

    @classmethod
    def load(cls, path: str, path_ref:str = None):
        """
        Method that loads the image and reference image from the paths
        and returns an instance of ImageSetHolo object.

        Parameters
        ----------
        path : str
            Path of the image file.
        path_ref : str, optional
            Path of the reference image, by default None

        Returns
        -------
        ImageSetHolo
            An instance of ImageSetHolo object containing the image and its metadata, 
            also the reference image and its metadata if it is loaded.

        Raises
        ------
        TypeError
            If the path or the path_ref is not a string, raise a TypeError.
        """
        if not isinstance(path, str):
            raise TypeError("The path must be a string.")
        image = hs.load(path, signal_type="hologram")
        if path_ref:
            if not isinstance(path_ref, str):
                raise TypeError("The path must be a string.")
            ref_image = hs.load(path_ref, signal_type="hologram")
            return cls(image, ref_image)
        return cls(image)

    def __save_ref_image(self, file, id_number: int):
        """
        Method that saves the reference image inside the NeXus file. It is used by the save method.

        Parameters
        ----------
        file : NXlinkgroup | NXgroup
            Opened NeXus file, in which the image is saved.
            The file is opened with function nxopen from nexusformat library.

        id_number : int
            Number of the imageset. Defines the order of the imagesets in the NeXus file.
        """
        if self.ref_image:
            self._ImageSet__save_image(
                file=file,
                key="ref_image",
                id_number=id_number, 
            )
        elif not self.ref_image and id_number == 0:
            print("No reference image is saved or already saved.")
        elif not self.ref_image and id_number > 0 and \
                file[f"raw_data/imageset_{id_number-1}"].attrs["type_measurement"] == "holography":
            print("The link to the previous reference image is saved.")
            file[f"raw_data/imageset_{id_number}/raw_images/ref_image"] = NXlink(
                f"raw_data/imageset_{id_number-1}/raw_images/ref_image"
            )
            file[f"raw_data/imageset_{id_number}/metadata/ref_image_metadata"] = NXlink(
                f"raw_data/imageset_{id_number-1}/metadata/ref_image_metadata"
            )
            file[
                f"raw_data/imageset_{id_number}/metadata/ref_image_original_metadata"
            ] = NXlink(
                f"raw_data/imageset_{id_number-1}/metadata/ref_image_original_metadata"
            )

    def save(self, path:str):
        """
        Method that saves the imageset in the NeXus file. It utilizes the __save_image 
        and __file_prep methods.

        Parameters
        ----------
        path : str
            Path of the NeXus file, in which the imageset is saved.
        """
        with nxopen(path, "a") as opened_file:
            id_number = self._ImageSet__file_prep(opened_file)
            self._ImageSet__save_image(file=opened_file, key="image", id_number=id_number)
            self.__save_ref_image(file=opened_file, id_number=id_number)

    @staticmethod
    def __load_image_from_nxs(
        file, key: str, id_number: int
    ):  # discuss, is there the need to redefine it just because of HologramImage instead of Signal2D?
        """
        Method that loads the image from the NeXus file. It is used by the load_from_nxs method.

        Parameters
        ----------
        file : NXlinkgroup | NXgroup
            Opened NeXus file, in which the image is saved.
            The file is opened with function nxopen from nexusformat library.
        
        key : str
            Key of the image in the images dictionary.
        
        id_number : int
            Number of the imageset. Defines the order of the imagesets in the NeXus file.

        Returns
        -------
        full_image : HologramImage
            A hyperspy object containing the image and its metadata.
        """
        image = file[f"raw_data/imageset_{id_number}/raw_images/{key}"]
        metadata = json.loads(
            file[f"raw_data/imageset_{id_number}/metadata/{key}_metadata"].nxdata
        )
        original_metadata = json.loads(
            file[f"raw_data/imageset_{id_number}/metadata/{key}_original_metadata"].nxdata
        )
        full_image = HologramImage(
            image.data,
            metadata=metadata,
            original_metadata=original_metadata,
        )
        if "units" in image.attrs:
            full_image.axes_manager[0].name = image.attrs["1_axis"]
            full_image.axes_manager[1].name = image.attrs["2_axis"]
            full_image.axes_manager[0].units = image.attrs["units"]
            full_image.axes_manager[1].units = image.attrs["units"]
            full_image.axes_manager[0].scale = image.attrs["scale"]
            full_image.axes_manager[1].scale = image.attrs["scale"]
        if not full_image.metadata["General"]["title"]:
            full_image.metadata["General"]["title"] = full_image.metadata["General"][
                "original_filename"
            ].split(".")[0]
        return full_image

    @classmethod
    def load_from_nxs(cls, path: str, id_number: int = 0):
        """
        Class method that loads the imageset from the NeXus file. It utilizes 
        the __load_image_from_nxs method.

        Parameters
        ----------
        path : str
            Path of the NeXus file, from which the imageset is loaded.
        id_number : int, optional
            Number of the imageset. Defines the order of the imagesets in the NeXus file, 
            by default 0

        Returns
        -------
        ImageSetHolo
            An instance of ImageSetHolo object containing the image and its metadata,
            also the reference image and its metadata if it is loaded.
        """
        with nxopen(path, "r") as opened_file:
            full_image = cls.__load_image_from_nxs(
                file=opened_file, key="image", id_number=id_number
            )
            if "ref_image" in opened_file[f"raw_data/imageset_{id_number}/raw_images"]:
                full_ref_image = cls.__load_image_from_nxs(
                    file=opened_file, key="ref_image", id_number=id_number
                )
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
        self.image.metadata["Signal"]["Holography"] = self.wave_image.metadata["Signal"][
            "Holography"
        ]
        self.image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
            "sb_position"
        ] = list(
            self.wave_image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
                "sb_position"
            ].data.astype("float")
        )
        self.image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
            "sb_size"
        ] = list(
            self.wave_image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
                "sb_size"
            ].data.astype("float")
        )
        self.image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
            "sb_smoothness"
        ] = list(
            self.wave_image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
                "sb_smoothness"
            ].data.astype("float")
        )
        if (
            self.wave_image.metadata["Signal"]["Holography"]["Reconstruction_parameters"][
                "sb_units"
            ]
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

    def save(self, path):
        super().save(path)

    @classmethod
    def load_from_nxs(cls, path, id_number=0):
        return super().load_from_nxs(path, id_number)
