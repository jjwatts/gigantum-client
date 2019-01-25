from setuptools import setup, find_packages
from codecs import open
from os import path
from gtmcore import __version__

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if x.startswith('git+')]

setup(
    name='gtmcore',
    version=__version__,
    description='Common tools and packages for the Gigantum Client application',
    long_description=long_description,
    license='MIT',
    classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
    ],
    keywords=[
            'gigantum',
            'open science'
        ],
    packages=find_packages(exclude=['docs', '*tests*']),
    package_data={'gtmcore': ['logging/*.default', 'configuration/config/*.default', 'labbook/*.default',
                              'dataset/*.default', 'dataset/storage/thumbnails/*.png']},
    include_package_data=True,
    author='Gigantum/FlashX LLC',
    install_requires=install_requires,
    dependency_links=dependency_links,
    author_email='support@gigantum.com'
)

