# -*- coding: utf-8 -*-

"""
Based on https://github.com/yuma-m/matplotlib-draggable-plot
"""

import math

import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
import os
from align_panel.data_structure import ImageSetHolo
import cv2

class DraggablePlotExample(object):
    u""" An example of plot with draggable markers """

    def __init__(self, ref_image, mov_image):
        self._figure, self._axes, self._line, self._line2 = None, None, None, None
        self._dragging_point = None
        self._colors = ['tab:blue','tab:orange','tab:green','tab:red','tab:purple','tab:brown','tab:pink','tab:gray','tab:olive','tab:cyan']
        self._points = []
        self._mov_points = []
        self._image_dict = {'ref': ref_image, 'mov': mov_image}
        

        self._init_plot()
        

    def _init_plot(self):
        self._figure, self._axes = plt.subplots(1, 2)
        for ax, image in zip(self._axes, self._image_dict.values()):
            ax.imshow(image, cmap='gray')
            ax.xaxis.set_tick_params(labelbottom=False)
            ax.yaxis.set_tick_params(labelleft=False)
        

        self._figure.canvas.mpl_connect('button_press_event', self._on_click)
        self._figure.canvas.mpl_connect('button_press_event', self._on_click_2)
        self._figure.canvas.mpl_connect('button_release_event', self._on_release)
        self._figure.canvas.mpl_connect('button_release_event', self._on_release_2)
        self._figure.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self._figure.canvas.mpl_connect('motion_notify_event', self._on_motion_2)

        plt.show()


    def _update_plot(self):
        if not self._points:
            self._line.set_data([], [])
        else:
            x, y = zip(*(self._points))
            # Add new plot
            if not self._line:
                self._line, = self._axes[0].plot(x, y,'.', markersize=13)
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
                self._line2, = self._axes[1].plot(x, y,'.', markersize=13)
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
        distance_threshold = 300.0
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
    result = DraggablePlotExample(image1, image2)
