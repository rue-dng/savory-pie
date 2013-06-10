#!/usr/bin/env python
import os
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

os.environ['DJANGO_SETTINGS_MODULE'] = 'savory_pie.tests.django.dummy_settings'
subprocess.call(['make', 'html'], cwd='docs')
subprocess.call(['open', 'index.html'], cwd='docs/_build/html')
