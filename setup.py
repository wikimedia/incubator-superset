# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import io
import json
import os
import subprocess
import sys

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py

if sys.version_info < (3, 6):
    sys.exit('Sorry, Python < 3.6 is not supported')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PACKAGE_DIR = os.path.join(BASE_DIR, 'superset', 'static', 'assets')
PACKAGE_FILE = os.path.join(PACKAGE_DIR, 'package.json')
with open(PACKAGE_FILE) as package_file:
    version_string = json.load(package_file)['version']

# -- wikimedia change
# set version string manually
# update this whenever we make a change or merge from upstream.
version_string = '0.32.0rc2-wikimedia1'


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
class WebpackBuildPyCommand(build_py):
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
                'build_py failed during webpack in {} with {}'.format(PACKAGE_DIR, retval),
                file=sys.stderr
            )

        # Now continue the usual build_py process.
        build_py.run(self)

setup(
    name='apache-superset',
    description=(
        'A modern, enterprise-ready business intelligence web application'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    version=version_string,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    # -- wikimedia change
    # Override the usual build_py phase to run webpack first.
    cmdclass={'build_py': WebpackBuildPyCommand},
    scripts=['superset/bin/superset'],
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'cors': ['flask-cors>=2.0.0'],
        'console_log': ['console_log==0.2.10'],
        'hive': [
            'pyhive>=0.4.0',
            'tableschema',
            'thrift-sasl>=0.2.1',
            'thrift>=0.9.3',
        ],
        'presto': ['pyhive>=0.4.0'],
        'gsheets': ['gsheetsdb>=0.1.9'],
    },
    author='Apache Software Foundation',
    author_email='dev@superset.incubator.apache.org',
    url='http://superset.apache.org/',
    download_url=(
        'https://dist.apache.org/repos/dist/release/superset/' + version_string
    ),
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
)
