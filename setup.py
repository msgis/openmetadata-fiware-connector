from setuptools import setup, find_packages

base_requirements = {"openmetadata-ingestion~=1.3.0"}

setup(
    name="fiware-connector",
    version="0.0.2",
    url="https://open-metadata.org/",
    author="Daniel Chenari",
    license="MIT license",
    description="Ingestion Framework for OpenMetadata",
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    install_requires=list(base_requirements),
    packages=find_packages(include=["connector", "connector.*"]),
)
