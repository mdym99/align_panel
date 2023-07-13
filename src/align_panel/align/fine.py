"""
Run in prototypes folder !!!
"""

import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
from skimage.transform import rescale
import matplotlib as mpl
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
from align_panel.image_transformer import ImageTransformer


class FineAlignments(object):

    def __init__(self, ref_image: np.array, mov_image: np.array, rebin: int, show_result = True):
            self._dict_images = {'ref': ref_image, 'mov': mov_image}
            self._steps = {'translate': 5, 'rotate': 2.5, 'scale': 0.75}
            self._rebin = rebin
            self._figure, self._axes = None, None
            self._image1 = None
            self._trans = None
            self._tmat = None
            self._result_image = None
            self._show_result = show_result

            self._init_plot()  

    def _on_press(self, event):
        sys.stdout.flush()
        if event.key == 'up':
            self._trans.translate(xshift=0., yshift=+self._steps['translate'])
        elif event.key == 'down':
            self._trans.translate(xshift=0., yshift=-self._steps['translate'])
        elif event.key == 'left':
            self._trans.translate(xshift=0. + self._steps['translate'], yshift=0.)
        elif event.key == 'right':
            self._trans.translate(xshift=0. - self._steps['translate'], yshift=0.)
        elif event.key == 'r':
            self._trans.rotate_about_center(rotation_degrees=-self._steps['rotate'])
        elif event.key == 'e':
            self._trans.rotate_about_center(rotation_degrees=self._steps['rotate'])
        elif event.key == '-':
            self._trans.uniform_scale_centered(scale_factor=1/self._steps['scale'])
        elif event.key == '+':
            self._trans.uniform_scale_centered(scale_factor=self._steps['scale'])
        elif event.key == 'enter':
            print(self._trans.get_combined_transform())
        elif event.key == 'escape':
            self._trans.clear_transforms()
        
        self._image1.set_data(self._trans.get_transformed_image())
        self._figure.canvas.draw()
    
    def _update_trans(self, val):
        self._steps['translate'] = val
    
    def _update_rot(self, val):
        self._steps['rotate'] = val
    
    def _update_scale(self, val):
        self._steps['scale'] = val

    def _on_close(self, event):
        self._tmat = self._trans.get_combined_transform()
        self._tmat.params[0, 2] *= self._rebin
        self._tmat.params[1, 2] *= self._rebin
        self._trans = ImageTransformer(self._dict_images['mov'])
        self._trans.add_transform(self._tmat)
        self._result_image = self._trans.get_transformed_image()
        if self._show_result:
            plt.figure('result')
            plt.imshow(self._dict_images['ref'], cmap='gray')
            plt.imshow(self._result_image, cmap='gray', alpha=0.5)
            plt.show()

    def _init_plot(self):
        ref_image = rescale(self._dict_images['ref'].copy(), 1/self._rebin, anti_aliasing=False)
        mov_image = rescale(self._dict_images['mov'].copy(), 1/self._rebin, anti_aliasing=False)
        self._figure, self._axes = plt.subplots()
        self._trans = ImageTransformer(mov_image)
        self._image1 = plt.imshow(mov_image, cmap = 'gray', interpolation='none')
        self._figure.canvas.mpl_connect('key_press_event', self._on_press)
        plt.imshow(ref_image, cmap = 'gray', alpha = 0.4,interpolation='none')
        self._figure.canvas.mpl_connect('close_event', self._on_close)

        self._figure.subplots_adjust(bottom=0.3, left = 0.2)
        slideraxis = self._figure.add_axes([0.16, 0.17, 0.75, 0.03])
        slider = Slider(slideraxis, label='Translation',
                        valmin=0, valmax=10, valinit=5, )
        slider.on_changed(self._update_trans)

        slideraxis_rot = self._figure.add_axes([0.16, 0.25, 0.03, 0.6])
        slider_rot = Slider(slideraxis_rot, label='Rotation',
                        valmin=0, valmax=5, valinit=2.5,orientation='vertical')
        slider_rot.on_changed(self._update_rot)

        
        slideraxis_scale = self._figure.add_axes([0.16, 0.07, 0.75, 0.03])
        slider_scale = Slider(slideraxis_scale, label='Scaling',
                        valmin=0.5, valmax=1, valinit=0.75)
        slider_scale.on_changed(self._update_scale)


        plt.show()  
        