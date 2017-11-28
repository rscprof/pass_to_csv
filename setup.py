"""A setuptools based setup module.

"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pass_to_csv',
    version='0.3',
    description='Pipe from passwordstore keeper to csv format',
    long_description=long_description,
    url='https://github.com/rscprof/pass_to_csv',
    author='Alexandr Glusker',
    author_email='rscprof@gmail.com',
    license='GPL3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Other Audience',
        'Topic :: Utilities',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='pass csv',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'pass_to_csv=pass_to_csv:main',
        ],
    },
    data_files=[
	('/usr/share/locale/en_US/LC_MESSAGES/',['locale/en_US/LC_MESSAGES/pass_to_csv.mo']),
	('/usr/share/locale/ru_RU/LC_MESSAGES/',['locale/ru_RU/LC_MESSAGES/pass_to_csv.mo'])
    ],
)

