import pathlib
from setuptools import setup
import setuptools

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="spodcast",
    version="0.3.3",
    description="A caching Spotify podcast to RSS proxy.",
    long_description='README.md',
    long_description_content_type="text/markdown",
    url="https://github.com/Yetangitu/spodcast.git",
    author="yetangitu",
    author_email="github-f@unternet.org",
    licence="GPLv3",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: PHP"
    ],
    packages=['spodcast'],
    entry_points ={
        'console_scripts': [
            'spodcast=spodcast.__main__:main'
        ]
    },
    install_requires=['librespot @ https://github.com/kokarare1212/librespot-python/archive/refs/heads/rewrite.zip'],
    include_package_data=True,
)
