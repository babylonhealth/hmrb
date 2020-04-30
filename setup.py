#!/usr/bin/env python
import os
from setuptools import setup, find_packages, Extension

extension_modules = ("core", "lang", "node", "protobuffer", "response_pb2")

try:
    from Cython.Build import cythonize

    # * Using Cython to compile
    extensions = cythonize(
        [f"hmrb/{module}.py" for module in extension_modules],
        compiler_directives={"language_level": "3str"},
    )
except ImportError:
    if all(
        [
            os.path.isfile(f"hmrb/{module}.c")
            for module in extension_modules
        ]
    ):
        # * Using pre-compiled C files
        extensions = [
            Extension(module, [f"hmrb/{module}.c"])
            for module in extension_modules
        ]
    else:
        # * Using native Python
        extensions = []

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

with open("README.md") as f:
    long_description = f.read()

setup(
    name="hmrb",
    version="1.0.0",
    packages=find_packages(".", exclude=("tests",)),
    zip_safe=False,
    include_package_data=False,
    description="Hammurabi",
    author="Babylon Health",
    author_email="kristian.boda@babylonhealth.com",
    url="https://github.com/babylonhealth/hmrb",
    license="Proprietary",
    long_description=long_description,
    long_description_content_type="text/markdown",
    setup_requires=["cython<0.30"],
    ext_modules=extensions,
    install_requires=install_requires,
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
    ],
)
