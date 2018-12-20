# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
import json
import os
import subprocess

from setuptools import find_packages, setup
from setuptools.command.sdist import sdist

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PACKAGE_DIR = os.path.join(BASE_DIR, 'superset', 'static', 'assets')
PACKAGE_FILE = os.path.join(PACKAGE_DIR, 'package.json')
with open(PACKAGE_FILE) as package_file:
    version_string = json.load(package_file)['version']

# -- wikimedia change
# set version string manually
# update this whenever we make a change or merge from upstream.
version_string = '0.26.3-wikimedia1'


with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()


def get_git_sha():
    try:
        s = subprocess.check_output(['git', 'rev-parse', 'HEAD'])
        return s.decode().strip()
    except Exception:
        return ''


GIT_SHA = get_git_sha()
version_info = {
    'GIT_SHA': GIT_SHA,
    'version': version_string,
}
print('-==-' * 15)
print('VERSION: ' + version_string)
print('GIT SHA: ' + GIT_SHA)
print('-==-' * 15)

with open(os.path.join(PACKAGE_DIR, 'version_info.json'), 'w') as version_file:
    json.dump(version_info, version_file)


# -- wikimedia change
def parse_requirements(filename):
    """ Load requirements from a pip requirements file"""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

# Read install_requires from requirements.txt.
INSTALL_REQUIRES = parse_requirements('requirements.txt')


# -- wikimedia change
class WebpackSdistCommand(sdist):
    """
    Runs webpack in static/assets during sdist.
    This will webpack up the javascript assets.
    This should accomplish much of what ./pypi_push does.
    """
    def run(self):
        import subprocess
        # Make sure node dependencies are installed with yarn (including webpack)
        subprocess.check_output(['yarn'], cwd=PACKAGE_DIR, stderr=subprocess.STDOUT)

        # Run the npm build process to run webpack, etc.
        # NOTE: for some reason npm run build is failing, whereas a direct
        # webpack succeeds. Just call webpack.
        # NOTE: Using subprocess fails, whereas os.system succeeds. Not sure why.
        retval = os.system(
            'cd {} && ./node_modules/.bin/webpack && cd {}'.format(PACKAGE_DIR, BASE_DIR)
        )
        if retval !=0:
            raise Exception(
                'sdist failed during webpack in {} with {}'.format(PACKAGE_DIR, retval),
                file=sys.stderr
            )

        # Now continue the usual sdist process.
        sdist.run(self)

setup(
    name='superset',
    description=(
        'A modern, enterprise-ready business intelligence web application'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    version=version_string,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    # Override the usual sdist phase to run webpack first.
    cmdclass={'sdist': WebpackSdistCommand},
    scripts=['superset/bin/superset'],
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'cors': ['flask-cors>=2.0.0'],
        'console_log': ['console_log==0.2.10'],
    },
    author='Maxime Beauchemin',
    author_email='maximebeauchemin@gmail.com',
    url='https://github.com/apache/incubator-superset',
    download_url=(
        'https://github.com'
        '/apache/incubator-superset/tarball/' + version_string
    ),
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
