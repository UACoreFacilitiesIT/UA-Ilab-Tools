import os
from setuptools import setup, find_packages


def readme(filename):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with open(full_path, 'r') as file:
        return file.read()


setup(
    name="ua_ilab_tools",
    version="2.1.1",
    packages=find_packages(),
    author="Stephen Stern, Rafael Lopez, Etienne Thompson",
    author_email="sterns1@email.arizona.edu",
    include_package_data=True,
    long_description=readme("README.md"),
    long_description_content_type='text/markdown',
    url="https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools",
    license="MIT",
    description=(
        "Tools that interact with Agilent's iLab REST architecture."),
    install_requires=[
        "bs4",
        "ua-generic-rest-api",
    ],
)
