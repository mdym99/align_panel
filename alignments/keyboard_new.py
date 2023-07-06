"""
Run in prototypes folder !!!
"""

import sys
import cv2
from functools import partial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import os
from align_panel.data_structure import ImageSetHolo
import matplotlib as mpl
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
from align_panel.image_transformer import ImageTransformer


def on_press(fig, trans, image1, event):

    sys.stdout.flush()
    if event.key == 'up':
        trans.translate(xshift=0., yshift=+step_size)
    elif event.key == 'down':
        trans.translate(xshift=0., yshift=-step_size)
    elif event.key == 'left':
        trans.translate(xshift=0. + step_size, yshift=0.)
    elif event.key == 'right':
        trans.translate(xshift=0. - step_size, yshift=0.)
    elif event.key == 'r':
        trans.rotate_about_center(rotation_degrees=-rot_size)
    elif event.key == 'e':
        trans.rotate_about_center(rotation_degrees=rot_size)
    elif event.key == '-':
        trans.uniform_scale_centered(scale_factor=1/scale_size)
    elif event.key == '+':
        trans.uniform_scale_centered(scale_factor=scale_size)
    elif event.key == 'enter':
        print(trans.get_combined_transform())
    elif event.key == 'escape':
        trans.clear_transforms()
        #trans.add_null_transform()

    trans_image = trans.get_transformed_image()
    image1.set_data(trans_image)
    fig.canvas.draw()

def update_trans(val):
    global step_size
    step_size = val

def update_rot(val):
    global rot_size
    rot_size = val 

def update_scale(val):
    global scale_size
    scale_size = val

def align_keyboard_input(ref_image, mov_image, rebin = 8):
    old_shape = ref_image.shape
    new_shape = (int(old_shape[1]/rebin), int(old_shape[0]/rebin))
    ref_image = cv2.resize(ref_image, new_shape)
    mov_image = cv2.resize(mov_image, new_shape)
    fig, ax = plt.subplots()
    trans = ImageTransformer(mov_image)
    image1 = plt.imshow(mov_image, cmap = 'gray', interpolation='none')
    fig.canvas.mpl_connect('key_press_event', partial(on_press, fig, trans, image1))
    image2 = plt.imshow(ref_image, cmap = 'gray', alpha = 0.4,interpolation='none')

    fig.subplots_adjust(bottom=0.3, left = 0.2)
    slideraxis = fig.add_axes([0.16, 0.17, 0.75, 0.03])
    slider = Slider(slideraxis, label='Translation',
                    valmin=0, valmax=10, valinit=5, )
    slider.on_changed(update_trans)

    slideraxis_rot = fig.add_axes([0.16, 0.25, 0.03, 0.6])
    slider_rot = Slider(slideraxis_rot, label='Rotation',
                    valmin=0, valmax=5, valinit=2.5,orientation='vertical')
    slider_rot.on_changed(update_rot)

    
    slideraxis_scale = fig.add_axes([0.16, 0.07, 0.75, 0.03])
    slider_scale = Slider(slideraxis_scale, label='Scaling',
                    valmin=0.5, valmax=1, valinit=0.75)
    slider_scale.on_changed(update_scale)


    plt.show()
    matrix = trans.get_combined_transform() # maybe add scale translation into ImageTransformer module
    matrix.params[0,2]= matrix.params[0,2]*rebin
    matrix.params[1,2]= matrix.params[1,2]*rebin
    return matrix


if __name__ == '__main__':
    # path1 = os.path.dirname(os.getcwd())+'/data/Hb-.dm3'
    # path2 = os.path.dirname(os.getcwd())+'/data/Rb-.dm3'
    # path3 = os.path.dirname(os.getcwd())+'/data/Hb+.dm3'
    # path4 = os.path.dirname(os.getcwd())+'/data/Rb+.dm3'
    # image_set1 = ImageSetHolo.load(path1, path2)
    # image_set2 = ImageSetHolo.load(path3, path4)
    # image_set1.phase_calculation()
    # image_set2.phase_calculation()
    # im1 = image_set1.unwrapped_phase.data
    # im2 = image_set2.unwrapped_phase.data
    path1 = os.path.dirname(os.getcwd()) + "/data/unwrapped_phase_1.png"
    path2 = os.path.dirname(os.getcwd()) + "/data/unwrapped_phase_2.png"
    image1 = cv2.imread(path1,0)
    image2 = cv2.imread(path2,0)
    step_size = 5
    rot_size = 2.5
    scale_size = 0.75
    x = align_keyboard_input(image1, image2)
    print(x.params)