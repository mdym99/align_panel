""" Module containing the FineAlignments class, which allows for fine alignment of two images.
The fine alignments are achieved by using the ImageTransformer class. User can use the keyboard
to translate, rotate and scale the image.
"""

import sys
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.widgets import Slider
from skimage.transform import rescale
from align_panel.image_transformer import ImageTransformer

mpl.rcParams["path.simplify"] = True
mpl.rcParams["path.simplify_threshold"] = 1.0


class FineAlignments:
    """Class for fine alignment of ``two images``. The inputs are two images, of ``numpy array`` 
    type, and the rebinning factor. The rebinning factor is used to speed up the alignment 
    process. the fine alignments are achieved by using the ImageTransformer class. User can 
    use the keyboard to translate, rotate and scale the image.
    For translation, the ``arrow keys`` are used. For rotation, the `r`` (right) and ``e`` (left)
    keys are used. To scale the image, the ``+`` and ``-`` keys are used. The ``enter`` key prints
    the current transformation matrix. The ``escape`` key clears the transformation matrix.
    Steps can be changed with sliders, which are displayed below the image.
    Results are transformation matrix and the transformed image.

    Atributes
    ----------
    _image_dict : dict
        Dictionary containing the reference and moving images.
    _params : dict
        Dictionary containing the rebinning factor and the show_result parameter.
    _steps : dict
        Dictionary containing the steps for translation, rotation and scaling.
    _figure : matplotlib.figure.Figure
        Figure object.
    _axes : matplotlib.axes.Axes
        Axes object.
    _image1 : matplotlib.image.AxesImage
        Image object.
    _trans : ImageTransformer
        ImageTransformer object. Used for image transformation, contains the moving image, 
        transformation matrices and functions for image transformation.
    _results : dict
        Dictionary containing the transformation matrix and the transformed image.

    Methods
    -------
    _init_plot()
        Initializes the plot. The reference image is displayed in the background. The moving
        image is displayed in the foreground. The moving image is transformed with the
        ImageTransformer class. The user can use the keyboard to translate, rotate and scale the
        image.
    _on_press(event)
        Callback function for key press events.
    _on_close(event)
        Callback function for close event. After the window is closed, the transformation matrix
        and the transformed image are saved in the _results dictionary.

    """

    def __init__(
        self,
        ref_image: np.array,
        mov_image: np.array,
        rebin: int,
        show_result: bool = True,
    ):
        """
        Parameters
        ----------
        ref_image : np.array
            Reference image.
        mov_image : np.array
            Moving image.
        rebin : int
            Rebinning factor.
        show_result : bool, optional
            If True, the result is displayed in a new window. The default is True.

        """
        self._image_dict = {"ref": ref_image, "mov": mov_image}
        self._params = {"rebin": rebin, "show_result": show_result}
        self._steps = {"translate": 5, "rotate": 2.5, "scale": 0.75}
        self._figure, self._axes = None, None
        self._image1 = None
        self._trans = None
        self._results = {"tmat": None, "result_image": None}

        self._init_plot()

    @property
    def _rebin(self):
        return self._params["rebin"]

    @property
    def _show_result(self):
        return self._params["show_result"]

    @property
    def result_image(self):
        return self._results["result_image"]

    @property
    def tmat(self):
        return self._results["tmat"]

    def _init_plot(self):
        """Initializes the plot. The reference image is displayed in the background. The moving
        image is displayed in the foreground. The moving image is transformed with the
        ImageTransformer class. The user can use the keyboard to translate, rotate and scale the
        image.

        """
        ref_image = rescale(
            self._image_dict["ref"].copy(), 1 / self._rebin, anti_aliasing=False
        )
        mov_image = rescale(
            self._image_dict["mov"].copy(), 1 / self._rebin, anti_aliasing=False
        )
        self._figure, self._axes = plt.subplots()
        self._trans = ImageTransformer(mov_image)
        self._image1 = plt.imshow(mov_image, cmap="gray", interpolation="none")
        self._figure.canvas.mpl_connect("key_press_event", self._on_press)
        plt.imshow(ref_image, cmap="gray", alpha=0.4, interpolation="none")
        self._figure.canvas.mpl_connect("close_event", self._on_close)

        self._figure.subplots_adjust(bottom=0.3, left=0.2)
        slideraxis = self._figure.add_axes([0.16, 0.17, 0.75, 0.03])
        slider = Slider(
            slideraxis,
            label="Translation",
            valmin=0,
            valmax=10,
            valinit=5,
        )
        slider.on_changed(self._update_trans)

        slideraxis_rot = self._figure.add_axes([0.16, 0.25, 0.03, 0.6])
        slider_rot = Slider(
            slideraxis_rot,
            label="Rotation",
            valmin=0,
            valmax=5,
            valinit=2.5,
            orientation="vertical",
        )
        slider_rot.on_changed(self._update_rot)

        slideraxis_scale = self._figure.add_axes([0.16, 0.07, 0.75, 0.03])
        slider_scale = Slider(
            slideraxis_scale, label="Scaling", valmin=0.5, valmax=1, valinit=0.75
        )
        slider_scale.on_changed(self._update_scale)

        plt.show()

    def _on_press(self, event):
        """Callback function for key press events.
        Translation is done with the arrow keys. Rotation is done with the ``r`` and ``e`` keys.
        Scaling is done with the ``+`` and ``-`` keys. The ``enter`` key prints the current
        transformation matrix. The ``escape`` key clears the transformation matrix.

        """
        sys.stdout.flush()
        if event.key == "up":
            self._trans.translate(xshift=0.0, yshift=+self._steps["translate"])
        elif event.key == "down":
            self._trans.translate(xshift=0.0, yshift=-self._steps["translate"])
        elif event.key == "left":
            self._trans.translate(xshift=0.0 + self._steps["translate"], yshift=0.0)
        elif event.key == "right":
            self._trans.translate(xshift=0.0 - self._steps["translate"], yshift=0.0)
        elif event.key == "r":
            self._trans.rotate_about_center(rotation_degrees=-self._steps["rotate"])
        elif event.key == "e":
            self._trans.rotate_about_center(rotation_degrees=self._steps["rotate"])
        elif event.key == "-":
            self._trans.uniform_scale_centered(scale_factor=1 / self._steps["scale"])
        elif event.key == "+":
            self._trans.uniform_scale_centered(scale_factor=self._steps["scale"])
        elif event.key == "enter":
            print(self._trans.get_combined_transform())
        elif event.key == "escape":
            self._trans.clear_transforms()

        self._image1.set_data(self._trans.get_transformed_image())
        self._figure.canvas.draw()

    def _update_trans(self, val):
        """Callback function for slider events. Updates the translation step size."""
        self._steps["translate"] = val

    def _update_rot(self, val):
        """Callback function for slider events. Updates the rotation step size."""
        self._steps["rotate"] = val

    def _update_scale(self, val):
        """Callback function for slider events. Updates the scaling step size."""
        self._steps["scale"] = val

    def _on_close(self, event):
        """Callback function for close event. Saves the transformation matrix and the transformed
        image. The translation is multiplied by the rebin factor, so it can be used on the original
        image. If ``show_result`` is set to ``True``, the transformed image is displayed.

        """
        del event
        self._results["tmat"] = self._trans.get_combined_transform()
        self._results["tmat"].params[0, 2] *= self._rebin
        self._results["tmat"].params[1, 2] *= self._rebin
        self._trans = ImageTransformer(self._image_dict["mov"])
        self._trans.add_transform(self._results["tmat"])
        self._results["result_image"] = self._trans.get_transformed_image()
        if self._show_result:
            plt.figure("result")
            plt.imshow(self._image_dict["ref"], cmap="gray")
            plt.imshow(self._results["result_image"], cmap="gray", alpha=0.5)
            plt.show()
