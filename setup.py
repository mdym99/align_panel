from setuptools import setup, find_packages

setup(
    name="align_panel",
    version='0.0.4',
    license='MIT',
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.7.5',
    install_requires=[
            "numpy",
            "hyperspy",
            "h5py",
            "scikit-image",
            "pystackreg",
            "nexusformat",
            "matplotlib",
        ],
    package_dir={"": "src"},
    packages=find_packages(where='src'),
    description="Package handling magnetic imaging data and tools for image alignments",
    long_description='''
Package handling magnetic imaging data and tools for image alignments
''',
    url="https://github.com/mdym99/align_panel",
    author="Michal Dymacek, Zdeněk Nekula, Matthew Bryan",
    keywords="electron holography, image alignment",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License (MIT)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Environment :: Console',
    ],
)
