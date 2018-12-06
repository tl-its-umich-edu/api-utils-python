#! /usr/bin/env python

from setuptools import setup

setup(
    name="umich-api",
    description="Python Umich API Utilities",
    long_description=open('README.md', 'r').read().strip(),
    long_description_content_type='test/markdown',
    author="University of Michigan Teaching and Learning Developers",
    url="https://github.com/tl-its-umich-edu/esb-utils-python",
    license=open('LICENSE', 'r').read().strip(),
    package='umich_api',
    packages=['umich_api'],
    package_data={'umich_api': ['apis.json']},
    install_requires=[
        'ratelimit>=2.2.0,<2.2.99',
        'requests>=2.20.0,<2.22.99',
    ],
    setup_requires=['setuptools_scm',],
    tests_require=[],
    classifiers=[
        'Programming Language :: Python',
    ],
    use_scm_version=True,
    zip_safe=False,
)
