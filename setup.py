#!/usr/bin/env python

from setuptools import setup

setup(
  name='Distutils',
  version='1.0',
  description='Tablo download utilities',
  license='UNLICENSE',
  author='Ken Wilder',
  keywords=['tablo'],
  url='https://github.com/kjwilder/tablo_downloader',
  packages=['tablo_downloader'],
  install_requires=["requests"],
  entry_points={"console_scripts": [
          'tld = tablo_downloader.tablo:main',
          'tldapis = tablo_downloader.apis:main']},
)
