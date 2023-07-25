Align Panel
===========
``align_panel`` is an python library for processing images acquired by magnetic imaging techniques. This library provides a procedure for loading and saving raw data and contains 
image alignment workflow usefull for techniques utilizing multi-acquisitions. Currently, data processing workflow is developed for image formats loadable by ``Hyperspy`` library and saved into ``NeXus`` format by ``nexusformat`` library.

# 1 Installation
This manual suppose that you are using the anaconda python distribution. To begin the installation, open the **Anaconda Powershell Prompt** command line.

## 1.1 Create a new environment

This is optional. Instalation of the library into a new environment will prevent any interaction with another libraries. If the library is installed into an already existing environment, pay extra attention to its dependencies.

To crate a new environment by anaconda:
```bash
conda create --name myenv
```
(see <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html> for more information).

Then, activate the new environment:
```bash
conda activate myenv
```

## 1.2 Installation
First, install pystackreg library:
```bash
conda install -c conda-forge pystackreg
```

Second, install the align_panel library:
```bash
pip install https://github.com/znekula/align_panel/releases/download/0.0.1/align_panel-0.0.1-py3-none-any.whl
```

Third, install jupyter notebook:
```bash
conda install -c anaconda jupyter
```

# 2 Important libraries

# 2.1 Hyperspy

To fully utilize the possibilities of ``align_panel`` library, knowledge of ``Hyperspy`` library is very important. ``align_panel`` loading and handling of images, its metadata and axes information is carried out by ``Hyperspy``. It's alignments are partialy used as well.
Documentation of ``Hyperspy``:
<http://hyperspy.org/hyperspy-doc/current/index.html>

# 2.2 nexusformat

To walk towards the open access of scientific data, our goal was to develop a uniform and efficient way of storing large amounts of data needed for calculations of magnetic configurations of meassured samples. Thats why **NeXus** is used, a folder-like structure format based on The Hierarchical Data Format version 5 (HDF5). With its use, several acqusitions can be saved in one file, together with all its metadata and alignment results. 
Documentation of ``nexusformat``:
<https://manual.nexusformat.org/>

# 3 Features

- ``data_structure`` - module capable of loading, handling and saving the experimental data
- ``image_transformer`` - module handling the transformation matrices and image transformations
- ``notebook_helpers`` - module contatining usefull functions for jupyter notebook, such as stop button, or function to adjust the width of the notebook window
- ``align`` - folder containing the alignments
    - ``crop`` - module for cropping the images and automatic alignments
    - ``fine`` - module for fine alignments with keyboard control
    - ``points`` - module for manual alignments with point definition

# 4 Automatic alignments

Currently used automatic alignments:
- phase cross correlation from ``Hyperspy`` library (<http://hyperspy.org/hyperspy-doc/current/api/hyperspy._signals.signal2d.html#hyperspy._signals.signal2d.estimate_image_shift>) and from ``scikit-image`` library (<https://scikit-image.org/docs/dev/api/skimage.registration.html#skimage.registration.phase_cross_correlation>).
- ``PyStackReg`` library (<https://pystackreg.readthedocs.io/en/latest/index.html>)

# 5 Examples

Examples can be found in the **examples** folder. With several notebooks and scripts, it is possible to get familiar with the library and its possibilities.

# 6 Tests

Very basic tests were created with the help of the ``pytest`` library situated in the **tests** folder.
