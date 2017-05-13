from setuptools import Command, find_packages, setup
import os

VERSION = '0.1.0'


class PublishCommand(Command):
    """
    Publish the source distribution to private Chevah PyPi server.
    """

    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self.cwd, (
            'Must be in package root: %s' % self.cwd)
        self.run_command('bdist_wheel')
        # Upload package to Chevah PyPi server.
        upload_command = self.distribution.get_command_obj('upload')
        upload_command.repository = u'chevah'
        self.run_command('upload')


distribution = setup(
    name="chevah-leaderboard",
    version=VERSION,
    maintainer='Adi Roiban',
    maintainer_email='adi.roiban@chevah.com',
    license='MIT',
    platforms='any',
    description="Leaderboard for the Chevah Project.",
    long_description="",
    url='http://www.chevah.com',
    namespace_packages=['chevah'],
    packages=find_packages('.'),
    package_data={
        'chevah.leaderboard': ['static/*', 'author-aliases.txt'],
        },
    scripts=['scripts/start-chevah-leaderboard.py'],
    install_requires=[
        'klein==17.2',
        ],
    extras_require = {
        'dev': [
            'mock',
            'nose',
            'pyflakes',
            'pep8',
            ],
    },
    test_suite = 'chevah.leaderboard.tests',
    cmdclass={
        'publish': PublishCommand,
        },
    )
