# -*- coding: utf-8 -*-

"""
Based on https://github.com/yuma-m/matplotlib-draggable-plot
"""

import math

import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
import os
from align_panel.data_structure import ImageSetHolo
from skimage.transform import rescale
from skimage.io import imread
import itertools
from align_panel.image_transformer import ImageTransformer
import numpy as np

class Point_definition_plots(object):
    u""" An example of plot with draggable markers """

    def __init__(self, ref_image: np.array, mov_image: np.array , rebin: int):
        self._figure, self._axes, self._line, self._line2 = None, None, None, None
        self._dragging_point = None
        self._colors = itertools.cycle(['tab:blue','tab:orange','tab:green','tab:red','tab:purple','tab:brown','tab:pink','tab:gray','tab:olive','tab:cyan'])
        self._points = []
        self._mov_points = []
        self._image_dict = {'ref': ref_image, 'mov': mov_image}
        self._rebin = rebin
        

        self._init_plot()
        

    def _init_plot(self):
        old_shape = self._image_dict['ref'].shape
        new_shape = (int(old_shape[1]/self._rebin), int(old_shape[0]/self._rebin))
        names = ['Reference image', 'Moving image']
        resized_images = list(map(lambda image: rescale(image.copy(), 1/self._rebin, anti_aliasing=False), self._image_dict.values()))
        self._figure, self._axes = plt.subplots(1, 2)
        for ax, image, name in zip(self._axes, resized_images, names):
            ax.imshow(image, cmap='gray', extent = [0, old_shape[0], old_shape[0], 0])
            #ax.xaxis.set_tick_params(labelbottom=False)
            #ax.yaxis.set_tick_params(labelleft=False)
            ax.set_title(name)
        #self._figure.canvas.blit(self._figure.bbox)
        

        self._figure.canvas.mpl_connect('button_press_event', self._on_click)
        self._figure.canvas.mpl_connect('button_press_event', self._on_click_2)
        self._figure.canvas.mpl_connect('button_release_event', self._on_release)
        self._figure.canvas.mpl_connect('button_release_event', self._on_release_2)
        self._figure.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self._figure.canvas.mpl_connect('motion_notify_event', self._on_motion_2)

        plt.show()
        self._points = np.array(self._points).reshape(-1,2)
        self._mov_points = np.array(self._mov_points).reshape(-1,2)

    def _update_plot(self):
        if not self._points:
            self._line.set_data([], [])
        else:
            x, y = zip(*(self._points))
            # Add new plot
            if not self._line:
                self._line, = self._axes[0].plot(x, y,'.', markersize=13, color = 'tab:orange')
            # Update current plot
            else:
                self._line.set_data(x, y)
        plt.draw()
    
    def _update_plot2(self):
        if not self._mov_points:
            self._line2.set_data([], [])
        else:
            x, y = zip(*(self._mov_points))
            # Add new plot
            if not self._line2:
                self._line2, = self._axes[1].plot(x, y,'.', markersize=13, color = 'tab:orange')
            # Update current plot
            else:
                self._line2.set_data(x, y)
        plt.draw()

    def _add_point(self, points, x, y=None):
        if isinstance(x, MouseEvent):
            x, y = int(x.xdata), int(x.ydata)
        points.append((x, y))
        return x, y

    def _remove_point(self,points, x,_):
        for point in points:
            if point[0] == x:
                points.remove(point)

    def _remove_point_1(self, x,_):
            for i in range(len(self._points)):
                if self._points[i][0] == x:
                    self._points.pop(i)
                    self._mov_points.pop(i)
                    break
    def _remove_point_2(self, x,_):
            for i in range(len(self._mov_points)):
                if self._mov_points[i][0] == x:
                    self._points.pop(i)
                    self._mov_points.pop(i)
                    break
            

    def _find_neighbor_point(self,points, event):
        u""" Find point around mouse position

        :rtype: ((int, int)|None)
        :return: (x, y) if there are any point around mouse else None
        """
        distance_threshold = 100.0
        nearest_point = None
        min_distance = math.sqrt(2 * (100 ** 2))
        for x, y in points:
            distance = math.hypot(event.xdata - x, event.ydata - y)
            if distance < min_distance:
                min_distance = distance
                nearest_point = (x, y)
        if min_distance < distance_threshold:
            return nearest_point
        return None

    def _on_click(self, event):
        u""" callback method for mouse click event

        :type event: MouseEvent
        """
        # left click
        if event.button == 1 and event.inaxes in [self._axes[0]]:
            point = self._find_neighbor_point(self._points,event)
            if point:
                self._dragging_point = point
            else:
                self._add_point(self._points,event)
                self._add_point(self._mov_points,event)
            self._update_plot()
            self._update_plot2()
        
        # right click
        elif event.button == 3 and event.inaxes in [self._axes[0]]:
            point = self._find_neighbor_point(self._points, event)
            if point:
                self. _remove_point_1(*point)
                #self._remove_point(self._mov_points,*point)
                self._update_plot()
                self._update_plot2()
        # right click in 2. image

    def _on_click_2(self, event):
         if event.button == 1 and event.inaxes in [self._axes[1]]:
            point = self._find_neighbor_point(self._mov_points, event)
            if point:
                self._dragging_point = point
            else:
                self._add_point(self._points,event)
                self._add_point(self._mov_points,event)
            self._update_plot()
            self._update_plot2()

         elif event.button == 3 and event.inaxes in [self._axes[1]]:
            point = self._find_neighbor_point(self._mov_points, event)
            if point:
                self._remove_point_2(*point)
                #self._remove_point(self._mov_points,*point)
                self._update_plot()
                self._update_plot2()

    def _on_release(self, event):
        u""" callback method for mouse release event

        :type event: MouseEvent
        """
        if event.button == 1 and event.inaxes in [self._axes[0]] and self._dragging_point:
            self._dragging_point = None
            self._update_plot()
    
    def _on_release_2(self, event):
        u""" callback method for mouse release event

        :type event: MouseEvent
        """
        if event.button == 1 and event.inaxes in [self._axes[1]] and self._dragging_point:
            self._dragging_point = None
            self._update_plot2()

    def _on_motion(self, event):
        u""" callback method for mouse motion event

        :type event: MouseEvent
        """
        if not self._dragging_point:
            return
        if event.xdata is None or event.ydata is None:
            return
        if event.inaxes in [self._axes[0]]:
            for i in range(len(self._points)):
                if self._points[i] == self._dragging_point:
                    self._points[i] = (int(event.xdata), int(event.ydata))
                    self._dragging_point  = (int(event.xdata), int(event.ydata))
                    break
            self._update_plot()

    def _on_motion_2(self, event):
        u""" callback method for mouse motion event

        :type event: MouseEvent
        """
        if not self._dragging_point:
            return
        if event.xdata is None or event.ydata is None:
            return
        if event.inaxes in [self._axes[1]]:
            for i in range(len(self._mov_points)):
                if self._mov_points[i] == self._dragging_point:
                    self._mov_points[i] = (int(event.xdata), int(event.ydata))
                    self._dragging_point  = (int(event.xdata), int(event.ydata))
                    break
            self._update_plot2()


def points_alignments(ref_image: np.array, mov_image: np.array, rebin: int, align_method: str):
    trans = ImageTransformer(mov_image)
    result_points = Point_definition_plots(ref_image.copy(), mov_image.copy(), rebin)
    trans.estimate_transform(result_points._points, result_points._mov_points, align_method)
    final_image = trans.get_transformed_image()
    matrix = trans.get_combined_transform()
    return final_image, matrix



if __name__ == "__main__":
    # path1 = os.path.dirname(os.getcwd()) + "/data/Hb-.dm3"
    # path2 = os.path.dirname(os.getcwd()) + "/data/Rb-.dm3"
    # path3 = os.path.dirname(os.getcwd()) + "/data/Hb+.dm3"
    # path4 = os.path.dirname(os.getcwd()) + "/data/Rb+.dm3"
    # image_set1 = ImageSetHolo.load(path1, path2)
    # image_set2 = ImageSetHolo.load(path3, path4)
    # image_set1.phase_calculation()
    # image_set2.phase_calculation()
    # image1 = image_set1.image.data
    # image2 = image_set2.image.data
    path1 = os.path.dirname(os.getcwd()) + "/data/unwrapped_phase_1.png"
    path2 = os.path.dirname(os.getcwd()) + "/data/unwrapped_phase_2.png"
    image1 = imread(path1,0)
    image2 = imread(path2,0)
    # result = Point_definition_plots(image1, image2)
    # trans = ImageTransformer(image2)
    # trans.estimate_transform(result._points, result._mov_points,method='euclidean')
    # final_image = trans.get_transformed_image()

    final_image, matrix = points_alignments(image1, image2, 16, 'euclidean')
    plt.figure('result')
    plt.imshow(image1, cmap='gray')
    plt.imshow(final_image, cmap='gray',alpha=0.5)
    plt.show()
    print(matrix)