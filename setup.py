#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages

version = '0.1'

setup(
    name='savory-pie',
    version=version,
    url='https://github.com/RueLaLa/savory_pie',
    description='A RESTful api libary with support for django',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'pytz',
        'python-dateutil',
    ],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
