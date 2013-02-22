#!/usr/bin/env python
import sys
import os
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

os.environ['DJANGO_SETTINGS_MODULE'] = 'savory_pie.tests.dummy_settings'
args = ['nosetests', '-w', PROJECT_ROOT]
args.extend(sys.argv[1:])
subprocess.call(args)
