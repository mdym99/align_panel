
from functools import partial
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


class CustomRectangleSelector(RectangleSelector):
    def _onmove(self, event):
        """
        Redefining the _onmove method to prevent the rectangle from changing
        shape when moving the center handle when some part of the rectangle is 
        outside of the image. With this function, the rectangle will not change size.

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


class UnscalableRectangleSelector(CustomRectangleSelector): # need for this class?
    """
    Redefining the extents setter function. With this approach, the rectangle
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

class CropOut(object):

    def __init__(self, ref_image,mov_image,rebin, align_method= None, inverse = None, sub_pixel = None):

        self._dict_images = {"ref": ref_image, "mov": mov_image}
        self._positions = {"ref": None, "mov": None}
        self.fig, self.ax = None,None
        self._centers = {"ref": None, "mov": None}
        self._translation = None
        self._cropped_images = {"ref": None, "mov": None}
        self._rebin = rebin
        self._selectors = []

        self._init_plot()
    
    def _select_callback(self, eclick, erelease):
        """
        Callback for line selection.

        *eclick* and *erelease* are the press and release events.
        """
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
    
    def _toggle_selector(self, event):
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
            self.fig.canvas.draw()
        if event.key == "enter":
            self._positions["ref"] = np.array([normal_round(x) for x in self._selectors[0].extents])
            self._centers["ref"] = np.array([normal_round(x) for x in self._selectors[0].center])
            self._positions["mov"] = np.array([normal_round(x) for x in self._selectors[1].extents])
            self._centers["mov"] = np.array([normal_round(x) for x in self._selectors[1].center])
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
                self._positions["mov"][0] = normal_round(self._centers["mov"][0] - shape_ref[0] / 2)
                self._positions["mov"][1] = normal_round(self._centers["mov"][0] + shape_ref[0] / 2)
                self._positions["mov"][2] = normal_round(self._centers["mov"][1] - shape_ref[1] / 2)
                self._positions["mov"][3] = normal_round(self._centers["mov"][1] + shape_ref[1] / 2)
            print("Images are prepared for alignment. Close the plot window to continue.")
        
    def _close_event(self,event):
        self.translation = self._centers["mov"] - self._centers["ref"]
        self._cropped_images['ref'] = self._dict_images['ref'][
            self._positions["ref"][2] : self._positions["ref"][3],
            self._positions["ref"][0] : self._positions["ref"][1],
        ]
        self._cropped_images['mov'] = self._dict_images['mov'][
            self._positions["mov"][2] : self._positions["mov"][3],
            self._positions["mov"][0] : self._positions["mov"][1],
        ]



    def _init_plot(self):
        original_shape = self._dict_images["ref"].shape
        resized_images = list(
        map(lambda image: rescale(image.copy(), 1/self._rebin, anti_aliasing=False), self._dict_images.values()))

        self.fig = plt.figure(layout="constrained")
        self.axs = self.fig.subplots(1, 2)
        names = ["Reference image", "Moving image"]
        for ax, selector_class, image, name in zip(
            self.axs,
            [CustomRectangleSelector, UnscalableRectangleSelector],
            resized_images,
            names,
        ):
            ax.imshow(
                image, cmap="gray", extent=[0, original_shape[1], original_shape[0], 0]
            )
            # ax.xaxis.set_tick_params(labelbottom=False)
            # ax.yaxis.set_tick_params(labelleft=False)
            ax.set_title(f"{name}")
            self._selectors.append(
                selector_class(
                    ax,
                    self._select_callback,
                    useblit=True,
                    button=[1],  # disable middle button
                    minspanx=5,
                    minspany=5,
                    spancoords="pixels",
                    interactive=True,
                    drag_from_anywhere=True,
                )
            )
        self.fig.canvas.mpl_connect(
            "key_press_event", self._toggle_selector)
        self.fig.canvas.mpl_connect('close_event', self._close_event)
        self.fig.canvas.draw()
        self.fig.suptitle(
            "To select square in second image, press space. Press enter to confirm."
        )
        plt.show()


def align_auto(ref_image, mov_image, method: str, inverse=True, sub_pixel_factor=2):
    if inverse:
        mov_image = -mov_image
    trans = ImageTransformer(mov_image)
    if method == "PyStackReg_translation":
        sr = StackReg(StackReg.TRANSLATION)
        matrix = sr.register(ref_image, mov_image)
        trans.add_transform(matrix)
    elif method == "PyStackReg_rigid":
        sr = StackReg(StackReg.RIGID_BODY)
        matrix = sr.register(ref_image, mov_image)
        trans.add_transform(matrix)
    elif method == "None":
        trans.add_null_transform()
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
        trans.translate(xshift=shifts[0], yshift=shifts[1])
    return trans.get_combined_transform()


class CropAlign(CropOut):
    
    def __init__(self, ref_image, mov_image, rebin=1, method="None", inverse=True, sub_pixel_factor=2):
        self._trans = None
        self._tmat = None
        self._result_image = None
        self._align_params = {"method": method, "inverse": inverse, "sub_pixel_factor": sub_pixel_factor}
        super().__init__(ref_image, mov_image, rebin=rebin)
        
        
    
    def _close_event(self, event):
        super()._close_event(event)
        matrix = align_auto(self._cropped_images['ref'], self._cropped_images['mov'], **self._align_params)
        self._trans = ImageTransformer(self._dict_images['mov'])
        self._trans.translate(self.translation[0], self.translation[1])
        self._trans.add_transform(matrix)
        self._tmat = self._trans.get_combined_transform()
        self._result_image = self._trans.get_transformed_image()
