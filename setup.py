import setuptools

# Use the readme file as the long description on PyPi
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='iridauploader',
    version='0.6.2',
    description='IRIDA uploader: upload NGS data to IRIDA system',
    url='https://github.com/phac-nml/irida-uploader',
    author='Jeffrey Thiessen',
    author_email='jeffrey.thiessen@canada.ca',
    long_description=long_description,
    long_description_content_type="text/markdown",
    # license specified on github
    license='Apache-2.0',
    keywords="IRIDA NGS uploader",
    packages=setuptools.find_packages(include=['iridauploader',
                                               'iridauploader.*',
                                               ]),
    install_requires=['rauth',
                      'requests',
                      'chardet',
                      'appdirs',
                      'cerberus',
                      'argparse',
                      'requests-toolbelt',
                      ],
    extras_require={
        "GUI": ["PyQt5==5.15.2", "PyQt5-stubs==5.14.2.2"],
        "TEST": ["selenium", "pytest"],
        "WINDOWS": ["pynsist"],
    },
    entry_points={
        'console_scripts': [
            'irida-uploader=iridauploader.core.cli:main',
            'irida-uploader-gui=iridauploader.gui.gui:main [GUI]',
            'integration-test=iridauploader.tests_integration.start_integration_tests:main [TEST]'
        ],
    },
    # https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    # Test cases makes make it incompatible with pre 3.5
    python_requires='>=3.5',

)
