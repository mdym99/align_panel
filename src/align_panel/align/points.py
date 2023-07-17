""" Module containing the class for the point definition alignment.

Based on https://github.com/yuma-m/matplotlib-draggable-plot
"""

import math

# import itertools - can be used for different colors of points
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from skimage.transform import rescale
from align_panel.image_transformer import ImageTransformer


class PointAlignments:
    """Class for the point definition alignment.
    The inputs are ``two images``, of ``numpy array`` type, and the rebinning factor.
    The rebinning factor is used to speed up the alignment process.
    When the class is initialized, two images are shown in two different axes.
    The user can select points in both images by left clicking. The points can be deleted
    by right clicking or dragged by left clicking. The points are later used for alignments
    with the use of the ``ImageTransformer`` class.

    Possible alignent techniques are:
           ``['affine', 'euclidean', 'similarity', 'projective']``
    By default, the euclidean alignment is used.

    """

    def __init__(
        self,
        ref_image: np.array,
        mov_image: np.array,
        rebin: int,
        method: str = "euclidean",
        show_result: bool = True,
    ):
        self._image_dict = {"ref": ref_image, "mov": mov_image}
        self._params = {"rebin": rebin, "method": method, "show_result": show_result}
        self._figure, self._axes, self._line, self._line2 = None, None, None, None
        self._dragging_point = None
        # self._colors = itertools.cycle(['tab:blue','tab:orange','tab:green','tab:red','tab:purple','tab:brown','tab:pink','tab:gray','tab:olive','tab:cyan'])
        self._points = []
        self._mov_points = []
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
    def result_image(self):
        return self._results["result_image"]

    @property
    def tmat(self):
        return self._results["tmat"]

    def _init_plot(self):
        """Initialize plot for point selection, connect events to callbacks."""
        original_shape = self._image_dict["ref"].shape
        names = ["Reference image", "Moving image"]
        resized_images = list(
            map(
                lambda image: rescale(
                    image.copy(), 1 / self._rebin, anti_aliasing=False
                ),
                self._image_dict.values(),
            )
        )
        self._figure, self._axes = plt.subplots(1, 2)
        for axis, image, name in zip(self._axes, resized_images, names):
            axis.imshow(
                image, cmap="gray", extent=[0, original_shape[1], original_shape[0], 0]
            )
            axis.set_title(name)
        self._figure.canvas.blit(self._figure.bbox)  # maybe increase performance
        self._figure.canvas.mpl_connect("button_press_event", self._on_click)
        self._figure.canvas.mpl_connect("button_press_event", self._on_click_2)
        self._figure.canvas.mpl_connect("button_release_event", self._on_release)
        self._figure.canvas.mpl_connect("button_release_event", self._on_release_2)
        self._figure.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self._figure.canvas.mpl_connect("motion_notify_event", self._on_motion_2)
        self._figure.canvas.mpl_connect("close_event", self._on_close)
        plt.show()

    def _update_plot(self):
        """Function called in ``_on_click`` to update the plot with the new points.
        Updates the plot in axis 1.

        """
        if not self._points:
            self._line.set_data([], [])
        else:
            x, y = zip(*(self._points))
            # Add new plot
            if not self._line:
                (self._line,) = self._axes[0].plot(
                    x, y, ".", markersize=13, color="tab:orange"
                )
            # Update current plot
            else:
                self._line.set_data(x, y)
        plt.draw()

    def _update_plot2(self):
        """Function called in ``_on_click_2`` to update the plot with the new points.
        Updates the plot in axis 2.

        """
        if not self._mov_points:
            self._line2.set_data([], [])
        else:
            x, y = zip(*(self._mov_points))
            # Add new plot
            if not self._line2:
                (self._line2,) = self._axes[1].plot(
                    x, y, ".", markersize=13, color="tab:orange"
                )
            # Update current plot
            else:
                self._line2.set_data(x, y)
        plt.draw()

    def _add_point(self, points, x, y=None):
        if isinstance(x, MouseEvent):
            x, y = int(x.xdata), int(x.ydata)
        points.append((x, y))
        return x, y

    def _remove_point_1(self, x, _):
        """Remove point from list of points. Called when right clicking on a point in axis 1."""
        for i in range(len(self._points)):
            if self._points[i][0] == x:
                self._points.pop(i)
                self._mov_points.pop(i)
                break

    def _remove_point_2(self, x, _):
        """Remove point from list of points. Called when right clicking on a point in axis 2."""
        for i in range(len(self._mov_points)):
            if self._mov_points[i][0] == x:
                self._points.pop(i)
                self._mov_points.pop(i)
                break

    def _find_neighbor_point(self, points, event):
        """Find point around mouse position.
        If found, return the point (x, y), otherwise return None.

        """
        distance_threshold = 100
        nearest_point = None
        min_distance = math.sqrt(2 * (100**2))
        for x, y in points:
            distance = math.hypot(event.xdata - x, event.ydata - y)
            if distance < min_distance:
                min_distance = distance
                nearest_point = (x, y)
        if min_distance < distance_threshold:
            return nearest_point
        return None

    def _on_click(self, event):
        """Callback method for mouse click event. Add point if left click, remove point if right
        click. If left click on a point, start dragging it. Function working with axis 1.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent

        """
        # left click
        if event.button == 1 and event.inaxes in [self._axes[0]]:
            point = self._find_neighbor_point(self._points, event)
            if point:
                self._dragging_point = point
            else:
                self._add_point(self._points, event)
                self._add_point(self._mov_points, event)
            self._update_plot()
            self._update_plot2()

        # right click
        elif event.button == 3 and event.inaxes in [self._axes[0]]:
            point = self._find_neighbor_point(self._points, event)
            if point:
                self._remove_point_1(*point)
                self._update_plot()
                self._update_plot2()

    def _on_click_2(self, event):
        """Callback method for mouse click event. Add point if left click, remove point if right
        click. If left click on a point, start dragging it. Function working with axis 2.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent

        """
        # left click
        if event.button == 1 and event.inaxes in [self._axes[1]]:
            point = self._find_neighbor_point(self._mov_points, event)
            if point:
                self._dragging_point = point
            else:
                self._add_point(self._points, event)
                self._add_point(self._mov_points, event)
            self._update_plot()
            self._update_plot2()

        # right click
        elif event.button == 3 and event.inaxes in [self._axes[1]]:
            point = self._find_neighbor_point(self._mov_points, event)
            if point:
                self._remove_point_2(*point)
                self._update_plot()
                self._update_plot2()

    def _on_release(self, event):
        """Callback method for mouse release event. Stop dragging point if left click. Function
        working with axis 1.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent

        """
        if (
            event.button == 1
            and event.inaxes in [self._axes[0]]
            and self._dragging_point
        ):
            self._dragging_point = None
            self._update_plot()

    def _on_release_2(self, event):
        """Callback method for mouse release event. Stop dragging point if left click. Function
        working with axis 1.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent

        """
        if (
            event.button == 1
            and event.inaxes in [self._axes[1]]
            and self._dragging_point
        ):
            self._dragging_point = None
            self._update_plot2()

    def _on_motion(self, event):
        """Callback method for mouse motion event. If dragging point, update its position. Function
        working with axis 1.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent

        """
        if not self._dragging_point:
            return
        if event.xdata is None or event.ydata is None:
            return
        if event.inaxes in [self._axes[0]]:
            for i in range(len(self._points)):
                if self._points[i] == self._dragging_point:
                    self._points[i] = (int(event.xdata), int(event.ydata))
                    self._dragging_point = (int(event.xdata), int(event.ydata))
                    break
            self._update_plot()

    def _on_motion_2(self, event):
        """Callback method for mouse motion event. If dragging point, update its position. Function
        working with axis 2.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent

        """
        if not self._dragging_point:
            return
        if event.xdata is None or event.ydata is None:
            return
        if event.inaxes in [self._axes[1]]:
            for i in range(len(self._mov_points)):
                if self._mov_points[i] == self._dragging_point:
                    self._mov_points[i] = (int(event.xdata), int(event.ydata))
                    self._dragging_point = (int(event.xdata), int(event.ydata))
                    break
            self._update_plot2()

    def _on_close(self, event):
        """Callback method for closing the figure.
        Points are transformed to numpy array and saved to ``self._points`` and
        ``self._mov_points``. Alignments from ``ImageTransformer`` are saved to self._tmat.
        If ``show_result`` is True, the result image is shown.
        Possible alignent techniques are:
            ``['affine', 'euclidean', 'similarity', 'projective']``
        By default, ``euclidean`` is used.

        """
        del event
        self._points = np.array(self._points).reshape(-1, 2)
        self._mov_points = np.array(self._mov_points).reshape(-1, 2)
        trans = ImageTransformer(self._image_dict["mov"])
        trans.estimate_transform(self._points, self._mov_points, method=self._method)
        self._results["result_image"] = trans.get_transformed_image()
        self._results["tmat"] = trans.get_combined_transform()
        if self._show_result:
            plt.figure("Result of alignment")
            plt.imshow(self._image_dict["ref"], cmap="gray")
            plt.imshow(self.result_image, cmap="gray", alpha=0.5)
            plt.show()
