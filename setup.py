from setuptools import setup, find_packages

setup(
    name="scanner-v3",
    version="3.0.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "aiofiles>=23.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
    ],
)
