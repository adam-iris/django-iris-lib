# coding:utf-8

import sys
from setuptools import setup, find_packages


setup(name='django-iris-lib',
      version='0.0.6',
      description='IRIS DMC common library',
      long_description=open('README.md').read(),
      classifiers=[],
      keywords='',
      author='Adam Clark',
      author_email='adam@iris.washington.edu',
      url='http://ds.iris.edu/',
      license='Apache 2',
      packages=find_packages(exclude=('examples','examples.*','www','www.*')),
      include_package_data=True,
      zip_safe=False,
      tests_require=[
          'nose',
          'mock'
      ],
      install_requires=[
          'Django>=1.8',
          'textile>=2.2.1',
          'iso3166>=0.6',
          'requests>=2.2.1',
      ],
      )
