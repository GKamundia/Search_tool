from setuptools import setup, find_packages

setup(
    name="search_tool",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        'scholarly==1.7.9',
        'pandas>=2.0.3',
        'thefuzz>=0.19.0',
        'tenacity>=8.2.3',
        'python-dotenv>=1.0.0'
    ],
)
