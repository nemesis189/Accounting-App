# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in financemod/__init__.py
from financemod import __version__ as version

setup(
	name='financemod',
	version=version,
	description='finance module',
	author='subin',
	author_email='subin@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
