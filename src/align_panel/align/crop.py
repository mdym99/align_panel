""" Module conttaining tools for cropping and automatic alignments of two numpy arrays.
The automatic alignments are achieved by using the ImageTransformer class. 

"""

import numpy as np
import matplotlib.pyplot as plt
from pystackreg import StackReg
from hyperspy._signals.signal2d import estimate_image_shift
from skimage.registration import phase_cross_correlation
from skimage.transform import rescale
from matplotlib.widgets import RectangleSelector
from align_panel.image_transformer import ImageTransformer


def normal_round(number: float):
    """Round a float to the nearest integer."""
    return int(number + 0.5)


def align_auto(
    ref_image: np.ndarray, mov_image: np.ndarray, method: str, inverse=True, sub_pixel_factor: int = 2
):
    """Automatic alignment of two images. As an input, the function takes two images, of
    ``numpy array`` type, and the method for alignment.

    Parameters
    ----------
    ref_image : np.ndarray
        Reference image.
    mov_image : np.ndarray
        Image to be aligned.
    method : str
        Method for alignment. The options are: ``PyStackReg_translation``, ``PyStackReg_rigid``,
        ``cross_corelation_hyperspy``, ``cross_corelation_skimage`` and ``None``.
    inverse : bool, optional
        If True, the image will be inverted before alignment. The default is True.
    sub_pixel_factor : int, optional
        Subpixel factor for cross corelation methods. The default is 2.

    Returns
    -------
    matrix : sktransform.AffineTransform
        Transformation matrix for the alignment.

    """
    if inverse:
        mov_image = -mov_image
    trans = ImageTransformer(mov_image)
    if method == "PyStackReg_translation":
        stack_reg = StackReg(StackReg.TRANSLATION)
        matrix = stack_reg.register(ref_image, mov_image)
        trans.add_transform(matrix)
    elif method == "PyStackReg_rigid":
        stack_reg = StackReg(StackReg.RIGID_BODY)
        matrix = stack_reg.register(ref_image, mov_image)
        trans.add_transform(matrix)
    elif method == "cross_corelation_hyperspy":
        shifts = estimate_image_shift(
            ref_image, mov_image, sub_pixel_factor=sub_pixel_factor
        )
        shifts = np.flip(shifts[0])
        trans.translate(xshift=shifts[0], yshift=shifts[1])
    elif method == "cross_corelation_skimage":
        shifts, error, phasediff = phase_cross_correlation(
            ref_image, mov_image, upsample_factor=sub_pixel_factor
        )
        del error, phasediff
        trans.translate(xshift=shifts[0], yshift=shifts[1])
    elif method == "None":
        trans.add_null_transform()

    return trans.get_combined_transform()


class FixedSizeSelector(RectangleSelector):
    def _onmove(self, event):
        """Redefining the _onmove method to prevent the rectangle from changing
        shape when moving the center handle when some part of the rectangle is
        outside of the image. With this function, the rectangle will not change size.

        Based on :
        https://stackoverflow.com/questions/75641934/matplotlib-fixed-size-when-dragging-rectangleselector

        """

        # Start bbox
        s_x0, s_x1, s_y0, s_y1 = self.extents
        start_width = np.float16(s_x1 - s_x0)
        start_height = np.float16(s_y1 - s_y0)

        super()._onmove(event)

        # Custom behavior only if selector is moving
        if not self._active_handle == "C":
            return

        # End bbox
        e_x0, e_x1, e_y0, e_y1 = self.extents
        end_width = np.float16(e_x1 - e_x0)
        end_height = np.float16(e_y1 - e_y0)

        if start_width != end_width:
            e_x0, e_x1 = s_x0, s_x1

        if start_height != end_height:
            e_y0, e_y1 = s_y0, s_y1

        self.extents = e_x0, e_x1, e_y0, e_y1


class UnscalableRectangleSelector(FixedSizeSelector):  # need for this class?
    """Redefining the extents setter function. With this approach, the rectangle
    will not change size, but still be moveable.

    """

    @property
    def extents(self):
        """Return (xmin, xmax, ymin, ymax)."""
        x0, y0, width, height = self._rect_bbox
        xmin, xmax = sorted([x0, x0 + width])
        ymin, ymax = sorted([y0, y0 + height])
        return xmin, xmax, ymin, ymax

    @extents.setter
    def extents(self, extents):
        # Update displayed shape
        self._draw_shape(extents)
        if self._interactive:
            # Update displayed handles
            self._corner_handles.set_data(*self.corners)  # no corners - comment
            self._edge_handles.set_data(*self.edge_centers)  # no edges - comment
            self._center_handle.set_data(*self.center)  # only center for moving
        self.set_visible(self.visible)
        self.update()


class CropAlignments:
    """Class for cropping and aligning images. The class is based on the
    ``matplotlib`` library and uses the ``RectangleSelector`` widget. Input images
    are ``numpy ndarray`` type. Resuls are aligned image and transformation matrix for
    the alignments, or cropped images when only cropping is performed.

    Attributes
    ----------
    _image_dict : dict
        Dictionary containing the reference and moving images.
    _params : dict
        Dictionary containing the rebinning factor, alignment method, inverse bool parameter,
        subpixel factor and show result bool parameter.
     _figure : matplotlib.figure.Figure
        Figure object.
    _axes : matplotlib.axes.Axes
        Axes object.
    _selectors : list
        List of selector widgets for the alignment.
    _trans: ImageTransformer
       ImageTransformer object. Used for image transformation, contains the moving image,
        transformation matrices and functions for image transformation.
    _results: dict
        Dictionary containing the transformation matrix and the transformed image.

    """

    def __init__(
        self,
        ref_image: np.ndarray,
        mov_image: np.ndarray,
        rebin: int = 8,
        method: str = "None",
        inverse: bool = True,
        sub_pixel_factor: int = 2,
        show_result: bool = True,
    ):
        """
        Parameters
        ----------
        ref_image : np.ndarray
            Reference image.
        mov_image : np.ndarray
            Image to be aligned.
        rebin : int, optional
            Rebinning factor for the images. The default is 8.
        method : str, optional
            Method for alignment. The options are: ``PyStackReg_translation``, ``PyStackReg_rigid``,
            ``cross_corelation_hyperspy``, ``cross_corelation_skimage`` and ``None``. The default is
            "None". For none, only cropping is performed, and corresponding translation is saved in
            the transformation matrix.
        inverse : bool, optional
            If True, the image will be inverted before alignment. The default is True.
        sub_pixel_factor : int, optional
            Subpixel factor for cross corelation methods. The default is 2.
        show_result : bool, optional
            If True, the result of the alignment will be shown. The default is True.

        """
        self._dict_images = {"ref": ref_image, "mov": mov_image}
        self._params = {
            "rebin": rebin,
            "method": method,
            "inverse": inverse,
            "sub_pixel_factor": sub_pixel_factor,
            "show_result": show_result,
        }
        self._positions = {"ref": None, "mov": None}
        self.figure, self.axes = None, None
        self._centers = {"ref": None, "mov": None}
        self._cropped_images = {"ref": None, "mov": None}
        self._selectors = []
        self._trans = None
        self._results = {"tmat": None, "result_image": None}

        self._init_plot()

    @property
    def _rebin(self):
        return self._params["rebin"]

    @property
    def _method(self):
        return self._params["method"]

    @property
    def _show_result(self):
        return self._params["show_result"]

    @property
    def tmat(self):
        return self._results["tmat"]

    @property
    def result_image(self):
        return self._results["result_image"]

    def _init_plot(self):
        """Initialize the plot and the selector widgets. The plot contains the reference
        and moving images. The selector widgets are used for cropping and alignment.

        """
        original_shape = self._dict_images["ref"].shape
        resized_images = list(
            map(
                lambda image: rescale(
                    image.copy(), 1 / self._rebin, anti_aliasing=False
                ),
                self._dict_images.values(),
            )
        )

        self.figure = plt.figure(layout="constrained")
        self.axes = self.figure.subplots(1, 2)
        names = ["Reference image", "Moving image"]
        for axis, selector_class, image, name in zip(
            self.axes,
            [FixedSizeSelector, FixedSizeSelector],
            resized_images,
            names,
        ):
            axis.imshow(
                image, cmap="gray", extent=[0, original_shape[1], original_shape[0], 0]
            )
            axis.set_title(f"{name}")
            self._selectors.append(
                selector_class(
                    axis,
                    self._select_callback,
                    useblit=True,
                    button=[1],
                    minspanx=5,
                    minspany=5,
                    spancoords="pixels",
                    interactive=True,
                    drag_from_anywhere=True,
                )
            )
        self.figure.canvas.mpl_connect("key_press_event", self._toggle_selector)
        self.figure.canvas.mpl_connect("close_event", self._close_event)
        self.figure.canvas.draw()
        self.figure.suptitle(
            "To select square in second image, press space. Press enter to confirm."
        )
        plt.show()

    def _select_callback(self, eclick, erelease):
        """Callback for line selection.

        *eclick* and *erelease* are the press and release events.
        """
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata

    def _toggle_selector(self, event):
        """Callback for key press event. Press 't' to toggle the selector on and off.
        Press 'space' to show the selector widget on the moving image, also to redraw the
        selector widget. Press 'enter' to save the reference image position and start the
        alignment. After pressing 'enter', close the figure to continue with the alignment.

        """
        if event.key == "t":
            for selector in self._selectors:
                name = type(selector).__name__
                if selector.active:
                    print(f"{name} deactivated.")
                    selector.set_active(False)
                else:
                    print(f"{name} activated.")
                    selector.set_active(True)
        if event.key == " ":
            self._selectors[1].set_visible(True)
            self._selectors[1].draw_shape(self._selectors[0].extents)
            self._selectors[1]._center_handle.set_data(*self._selectors[0].center)
            self._selectors[1]._edge_handles.set_data(*self._selectors[0].edge_centers)
            self._selectors[1]._corner_handles.set_data(*self._selectors[0].corners)
            self.figure.canvas.draw()
        if event.key == "enter":
            self._positions["ref"] = np.array(
                [normal_round(x) for x in self._selectors[0].extents]
            )
            self._centers["ref"] = np.array(
                [normal_round(x) for x in self._selectors[0].center]
            )
            self._positions["mov"] = np.array(
                [normal_round(x) for x in self._selectors[1].extents]
            )
            self._centers["mov"] = np.array(
                [normal_round(x) for x in self._selectors[1].center]
            )
            shape_ref = np.array(
                [
                    self._positions["ref"][1] - self._positions["ref"][0],
                    self._positions["ref"][3] - self._positions["ref"][2],
                ]
            )
            shape_mov = np.array(
                [
                    self._positions["mov"][1] - self._positions["mov"][0],
                    self._positions["mov"][3] - self._positions["mov"][2],
                ]
            )
            if np.any(shape_ref != shape_mov):
                self._positions["mov"][0] = normal_round(
                    self._centers["mov"][0] - shape_ref[0] / 2
                )
                self._positions["mov"][1] = normal_round(
                    self._centers["mov"][0] + shape_ref[0] / 2
                )
                self._positions["mov"][2] = normal_round(
                    self._centers["mov"][1] - shape_ref[1] / 2
                )
                self._positions["mov"][3] = normal_round(
                    self._centers["mov"][1] + shape_ref[1] / 2
                )
            print(
                "Images are prepared for alignment. Close the plot window to continue."
            )

    def _close_event(self, event):
        """Callback for close event. Start the alignment after closing the plot window.
        
        """
        del event
        translation = self._centers["mov"] - self._centers["ref"]
        self._cropped_images["ref"] = self._dict_images["ref"][
            self._positions["ref"][2] : self._positions["ref"][3],
            self._positions["ref"][0] : self._positions["ref"][1],
        ]
        self._cropped_images["mov"] = self._dict_images["mov"][
            self._positions["mov"][2] : self._positions["mov"][3],
            self._positions["mov"][0] : self._positions["mov"][1],
        ]
        self._trans = ImageTransformer(self._dict_images["mov"])
        self._trans.translate(translation[0], translation[1])
        matrix = align_auto(
            self._cropped_images["ref"],
            self._cropped_images["mov"],
            self._method,
            self._params["inverse"],
            self._params["sub_pixel_factor"],
        )
        self._trans.add_transform(matrix)
        self._results["tmat"] = self._trans.get_combined_transform()
        self._results["result_image"] = self._trans.get_transformed_image()
        if self._show_result:
            plt.figure("result")
            plt.imshow(self._dict_images["ref"], cmap="gray")
            plt.imshow(self.result_image, cmap="gray", alpha=0.5)
            plt.show()
