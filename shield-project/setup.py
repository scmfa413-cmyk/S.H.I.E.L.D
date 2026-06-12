from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="shield-ai",
    version="0.1.0",
    author="Shield Project",
    description="Strategic Heuristic Intelligence for Logistics, Data & Operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/shield",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "pydantic>=2.0",
        "pydantic-settings>=2.0",
        "PyYAML>=6.0",
        "typer>=0.9.0",
        "rich>=13.0",
        "langchain>=0.1.0",
        "chromadb>=0.4.0",
        "httpx>=0.25.0",
    ],
    entry_points={
        "console_scripts": [
            "shield=shield.cli.main:app",
        ],
    },
)
