import re
import requests
from pypi_cli import get_package
import sys
import os

text = open(os.path.join(os.path.dirname(__file__), 'setup.py')).read()
version = re.search('version *= *[\'"]([0-9.a-z]+)[\'"]', text).group(1)
name = re.search('name *= *[\'"]([^"\']+)[\'"]', text).group(1)
pack = get_package(name, requests.Session())
versions = set(pack.version_downloads.keys())

if version in versions:
    sys.exit(1)
