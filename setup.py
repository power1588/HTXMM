from setuptools import setup, find_packages

setup(
    name="htx_ccxt",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "aiohttp>=3.9.1",
    ],
    python_requires=">=3.8",
) 