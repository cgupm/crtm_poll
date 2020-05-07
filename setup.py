#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = ['pip>=19', 'Click>=7.0', 'click-log>=0.3', 'aiohttp>=3.6',
                'filelock>=3']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', 'pytest-asyncio>=0.10']

setup(
    author="cgupm",
    author_email='cgupm@autistici.org',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python scripts for polling different data from CRTM.",
    entry_points={
        'console_scripts': [
            'crtm_poll=crtm_poll.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme,
    include_package_data=True,
    keywords='crtm_poll',
    name='crtm_poll',
    packages=find_packages(include=['crtm_poll', 'crtm_poll.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/cgupm/crtm_poll',
    version='0.2.0',
    zip_safe=False,
)
