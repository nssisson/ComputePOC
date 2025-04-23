from setuptools import setup, find_packages

setup(
    name="src",           # your package name
    version="0.1.0",
    packages=find_packages(),       # auto‐discover modules under this dir
    install_requires=[              # any runtime deps
        # e.g., "requests>=2.0"
    ],
)