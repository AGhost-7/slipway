from setuptools.command.install import install
from setuptools import setup, find_packages

setup(
    name = 'slipway',
    packages = find_packages(),
    version = '0.4.2',
    description = 'CLI tool for managing development containers',
    author = 'Jonathan Boudreau',
    author_email = 'jonathan.boudreau.92@gmail.com',
    url = 'https://github.com/AGhost-7/slipway',
    download_url = '',
    keywords = ['docker', 'development'],
    classifiers = [],
    install_requires = [
        'docker >= 3.0.0'
    ],
    entry_points = { 
        'console_scripts': [
            'slipway=slipway:main'
        ]
    }
)
