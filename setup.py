from setuptools import setup, find_packages

setup(
    name="align_panel",
    version='0.0.2',
    license='MIT',
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.7.5',
    install_requires=[
            "numpy",
            "hyperspy",
            "h5py",
            "scikit-image",
            "panel",
            "pystackreg",
            "nexusformat",
            "aperture @ https://github.com/znekula/align_panel/releases/download/0.0.1/aperture-0.0.1.tar.gz",
        ],
    package_dir={"": "src"},
    packages=find_packages(where='src'),
    entry_points={
        'console_scripts': [
            'align_panel=align_panel.cli:main',
        ]},
    description="Package to align images in HDF5 format",
    long_description='''
Package to align images in HDF5 format
''',
    url="https://github.com/znekula/align_panel",
    author="Zdeněk Nekula, Matthew Bryan",
    keywords="electron holography, image alignment",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License (MIT)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Environment :: Web Environment',
        'Environment :: Console',
    ],
)
