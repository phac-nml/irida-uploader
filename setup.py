import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='irida-uploader',
    version='0.4.0',
    description='IRIDA uploader: upload NGS data to IRIDA system',
    url='https://https://github.com/phac-nml/irida-uploader',
    author='Jeffrey Thiessen',
    author_email='jeffrey.thiessen@canada.ca',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='Apache-2.0',
    keywords="IRIDA NGS uploader",
    packages=setuptools.find_packages(include=['__app__',
                                               '__app__.*',
                                               ]),
    install_requires=['rauth',
                      'autopep8',
                      'pycodestyle',
                      'requests',
                      'appdirs',
                      'pytest',
                      'mkdocs',
                      'cerberus',
                      'argparse',
                      'selenium',
                      ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache-2.0 License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    python_requires='>=3.5',

)
