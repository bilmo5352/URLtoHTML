from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="url-to-html",
    version="0.1.0",
    author="",
    description="A Python library that fetches HTML content from URLs using progressive fallback strategy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
    ],
    extras_require={
        "fast": ["lxml>=4.6.0"],
    },
)

