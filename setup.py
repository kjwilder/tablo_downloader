#!/usr/bin/env python

from setuptools import setup

setup(
  name='tablo_downloader',
  version='1.0',
  description='Tablo download utilities',
  license='UNLICENSE',
  author='Ken Wilder',
  keywords=['tablo', 'api', 'download'],
  url='https://github.com/kjwilder/tablo_downloader',
  packages=['tablo_downloader'],
  install_requires=["requests"],
  entry_points={"console_scripts": [
          'tldl = tablo_downloader.tablo:main',
          'tldlapis = tablo_downloader.apis:main']},
)
