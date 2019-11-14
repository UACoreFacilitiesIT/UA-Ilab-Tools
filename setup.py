import os
from setuptools import setup, find_packages


def readme(filename):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with open(full_path, 'r') as file:
        return file.read()


setup(
    name="ua_ilab_tools",
    version="1.0.2",
    packages=find_packages(),
    author="Stephen Stern, Rafael Lopez, Etienne Thompson",
    author_email="sterns1@email.arizona.edu",
    include_package_data=True,
    description=(
        "Tools that interact with Agilent's iLab REST architecture."),
    long_description=readme("README.md"),
    long_description_content_type='text/markdown',
    url="https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools",
    license="MIT",
)
