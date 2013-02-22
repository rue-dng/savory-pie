#!/usr/bin/env python
import sys
import os
import subprocess

os.environ['DJANGO_SETTINGS_MODULE'] = 'savory_pie.tests.dummy_settings'
args = ['nosetests']
args.extend(sys.argv[1:])
subprocess.call(args)
