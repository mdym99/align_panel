import os
from functools import partial
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pystackreg import StackReg
from hyperspy._signals.signal2d import estimate_image_shift
from skimage.registration import phase_cross_correlation
from matplotlib.widgets import RectangleSelector
from align_panel.data_structure import ImageSetHolo
from align_panel.image_transformer import ImageTransformer




def normal_round(number):
    """Round a float to the nearest integer."""
    return int(number + 0.5)


class CustomRectangleSelector(RectangleSelector):
    def _onmove(self, event):
        """
        Redefining the _onmove method to prevent the rectangle from changing
        shape when moving the center handle outside of the image.
        With this function, the rectangle will not change size.
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


class UnscalableRectangleSelector(CustomRectangleSelector):
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
            self._corner_handles.set_data(*self.corners)  # no corners
            self._edge_handles.set_data(*self.edge_centers)  # no edges
            self._center_handle.set_data(*self.center)  # only center for moving
        self.set_visible(self.visible)
        self.update()


def select_callback(eclick, erelease):
    """
    Callback for line selection.

    *eclick* and *erelease* are the press and release events.
    """
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata


def toggle_selector(selectors, fig, centers, positions, event):
    if event.key == "t":
        for selector in selectors:
            name = type(selector).__name__
            if selector.active:
                print(f"{name} deactivated.")
                selector.set_active(False)
            else:
                print(f"{name} activated.")
                selector.set_active(True)
    if event.key == " ":
        selectors[1].set_visible(True)
        selectors[1].draw_shape(selectors[0].extents)
        selectors[1]._center_handle.set_data(*selectors[0].center)
        selectors[1]._edge_handles.set_data(*selectors[0].edge_centers)
        selectors[1]._corner_handles.set_data(*selectors[0].corners)
        fig.canvas.draw()
    if event.key == "enter":
        positions["ref"] = np.array([normal_round(x) for x in selectors[0].extents])
        centers["ref"] = np.array([normal_round(x) for x in selectors[0].center])
        positions["mov"] = np.array([normal_round(x) for x in selectors[1].extents])
        centers["mov"] = np.array([normal_round(x) for x in selectors[1].center])
        shape_ref = np.array(
            [
                positions["ref"][1] - positions["ref"][0],
                positions["ref"][3] - positions["ref"][2],
            ]
        )
        shape_mov = np.array(
            [
                positions["mov"][1] - positions["mov"][0],
                positions["mov"][3] - positions["mov"][2],
            ]
        )
        if np.any(shape_ref != shape_mov):
            positions["mov"][0] = normal_round(centers["mov"][0] - shape_ref[0] / 2)
            positions["mov"][1] = normal_round(centers["mov"][0] + shape_ref[0] / 2)
            positions["mov"][2] = normal_round(centers["mov"][1] - shape_ref[1] / 2)
            positions["mov"][3] = normal_round(centers["mov"][1] + shape_ref[1] / 2)
        print("Images are prepared for alignment. Close the plot window to continue.")


def align_auto(ref_image, mov_image, align_type: str, inverse=True, sub_pixel_factor=2):
    if inverse:
        mov_image = -mov_image
    trans = ImageTransformer(mov_image)
    if align_type == "PyStackReg_translation":
        sr = StackReg(StackReg.TRANSLATION)
        matrix = sr.register(ref_image, mov_image)
        trans.add_transform(matrix)
    elif align_type == "PyStackReg_rigid":
        sr = StackReg(StackReg.RIGID_BODY)
        matrix = sr.register(ref_image, mov_image)
        trans.add_transform(matrix)
    elif align_type == "None":
        trans.add_null_transform()
    elif align_type == "cross_corelation_hyperspy":
        shifts = estimate_image_shift(
            ref_image, mov_image, sub_pixel_factor=sub_pixel_factor
        )
        shifts = np.flip(shifts[0])
        trans.translate(xshift=shifts[0], yshift=shifts[1])
    elif align_type == "cross_corelation_skimage":
        shifts, error, phasediff = phase_cross_correlation(
            ref_image, mov_image, upsample_factor=sub_pixel_factor
        )
        trans.translate(xshift=shifts[0], yshift=shifts[1])
    return trans.get_combined_transform()


def crop_images(ref_image, mov_image, rebin=8):
    full_images = [ref_image, mov_image]
    original_shape = ref_image.shape
    new_shape = (int(original_shape[0] / rebin), int(original_shape[1] / rebin))
    resized_images = list(
        map(lambda image: cv2.resize(image.copy(), new_shape), full_images)
    )

    fig = plt.figure(layout="constrained")
    axs = fig.subplots(1, 2)
    selectors = []
    centers = {"ref": None, "mov": None}
    positions = {"ref": None, "mov": None}
    names = ["Reference image", "Moving image"]
    for ax, selector_class, image, name in zip(
        axs,
        [CustomRectangleSelector, UnscalableRectangleSelector],
        resized_images,
        names,
    ):
        ax.imshow(
            image, cmap="gray", extent=[0, original_shape[0], original_shape[1], 0]
        )
        # ax.xaxis.set_tick_params(labelbottom=False)
        # ax.yaxis.set_tick_params(labelleft=False)
        ax.set_title(f"{name}")
        selectors.append(
            selector_class(
                ax,
                select_callback,
                useblit=True,
                button=[1],  # disable middle button
                minspanx=5,
                minspany=5,
                spancoords="pixels",
                interactive=True,
                drag_from_anywhere=True,
            )
        )
    fig.canvas.mpl_connect(
        "key_press_event", partial(toggle_selector, selectors, fig, centers, positions)
    )
    fig.canvas.draw()
    fig.suptitle(
        "To select square in second image, press space. Press enter to confirm."
    )
    plt.show()

    translation = centers["mov"] - centers["ref"]
    crop_ref = full_images[0][
        positions["ref"][2] : positions["ref"][3],
        positions["ref"][0] : positions["ref"][1],
    ]
    crop_mov = full_images[1][
        positions["mov"][2] : positions["mov"][3],
        positions["mov"][0] : positions["mov"][1],
    ]
    return crop_ref, crop_mov, translation


def align_auto_crop(
    ref_image, mov_image, align_type: str, inverse=True, sub_pixel_factor=2
):
    trans = ImageTransformer(mov_image)
    crop_ref, crop_mov, translation = crop_images(ref_image, mov_image)
    trans.translate(xshift=translation[0], yshift=translation[1])
    auto_align_matrix = align_auto(
        crop_ref,
        crop_mov,
        align_type=align_type,
        inverse=inverse,
        sub_pixel_factor=sub_pixel_factor,
    )
    trans.add_transform(auto_align_matrix)
    return trans.get_combined_transform(), trans.get_transformed_image()


if __name__ == "__main__":
    path1 = os.path.dirname(os.getcwd()) + "/data/Hb-.dm3"
    path2 = os.path.dirname(os.getcwd()) + "/data/Rb-.dm3"
    path3 = os.path.dirname(os.getcwd()) + "/data/Hb+.dm3"
    path4 = os.path.dirname(os.getcwd()) + "/data/Rb+.dm3"
    image_set1 = ImageSetHolo.load(path1, path2)
    image_set2 = ImageSetHolo.load(path3, path4)
    image_set1.phase_calculation()
    image_set2.phase_calculation()
    image1 = image_set1.unwrapped_phase.data
    image2 = image_set2.unwrapped_phase.data
    x, image = align_auto_crop(image1, image2, "cross_corelation_hyperspy")
    plt.figure("result")
    plt.imshow(image1, cmap="gray")
    plt.imshow(image, cmap="gray", alpha=0.4)
    plt.show()
