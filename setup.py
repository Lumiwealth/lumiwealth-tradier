from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lumiwealth-tradier",
    version="0.1.6",
    author="David MacLeod and Robert Grzesik",
    description="lumiwealth-tradier is a Python package that serves as a wrapper for the Tradier brokerage API. "
    "This package simplifies the process of making API requests, handling responses, and performing various trading "
    "and account management operations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Lumiwealth/lumiwealth-tradier",
    packages=find_packages(),
    project_urls={"Bug Tracker": "https://github.com/Lumiwealth/lumiwealth-tradier/issues"},
    keywords="tradier finance api",
    install_requires=["pandas>=2.0.0", "numpy"],
    python_requires=">=3.9",
)
