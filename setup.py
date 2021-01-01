import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="w8-danielfett",
    version="0.0.1",
    author="Daniel Fett",
    author_email="mail@danielfett.de",
    description="Software for reading and programming the Brunner W8 GasControl gas scale.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/danielfett/w8",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "gatt",
    ],
    entry_points={
        "console_scripts": [
            "w8=w8.console:run",
        ],
    },
)