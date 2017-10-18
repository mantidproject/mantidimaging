#!/usr/bin/env python

import os
from distutils.core import Command
from setuptools import setup, find_packages
from sphinx.setup_command import BuildDoc

THIS_PATH = os.path.dirname(__file__)


class PublishDocsToGitHubPages(Command):
    description = 'Deploy built documentation to GitHub Pages'
    user_options = [
            ('repo=', 'r', 'Repository URL'),
            ('docs-dir=', 'd', 'Directory of documentation to publish'),
            ('commit-msg=', 'm', 'Commit message')
        ]

    def initialize_options(self):
        self.repo = None
        self.docs_dir = None
        self.commit_msg = None

    def finalize_options(self):
        self.repo = 'git@github.com:mantidproject/mantidimaging.git' \
            if self.repo is None else self.repo

        self.docs_dir = 'docs/build/html' \
            if self.docs_dir is None else self.docs_dir

        self.commit_msg = 'Publish documentation' \
            if self.commit_msg is None else self.commit_msg

    def run(self):
        git_dir = os.path.join(self.docs_dir, '.git')
        if os.path.exists(git_dir):
            import shutil
            shutil.rmtree(git_dir)

        from git import Git
        g = Git(self.docs_dir)
        g.init()
        g.add('.')
        g.commit('-m {}'.format(self.commit_msg))
        g.push('--force', self.repo, 'master:gh-pages')


setup(
    name='mantidimaging',
    version='0.9',
    packages=find_packages(),
    py_modules=['mantidimaging'],
    entry_points={
        'console_scripts': [
            'mantidimaging = mantidimaging.main:cli_main',
            'mantidimaging-ipython = mantidimaging.ipython:main'
        ],
        'gui_scripts': [
            'mantidimaging-gui = mantidimaging.main:gui_main'
        ]
    },
    url='https://github.com/mantidproject/mantidimaging',
    license='GPL-3.0',
    author='Dimitar Tasev',
    author_email='dimitar.tasev@stfc.ac.uk',
    description='MantidImaging Tomographic Reconstruction package',
    long_description=open("README.md").read(),
    platforms=["Linux"],
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Natural Language :: English',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Topic :: Scientific/Engineering',
        'Topic :: Imaging',
        'Topic :: Tomographic Reconstruction',
    ],
    cmdclass={
        'docs': BuildDoc,
        'docs_publish': PublishDocsToGitHubPages
    },
    extras_require={
        'testing': [
            'nose',
            'nose-randomly'
        ],
    },
    tests_require=[
        'nose',
        'nose-randomly'
    ],
    install_requires=[
        'numpy'
    ]
)
