
import codecs
import os.path
import re
from setuptools import setup


project_root = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(project_root, *parts), encoding='UTF-8') as f:
        return f.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.MULTILINE)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def long_description():
    readme_filename = os.path.join(project_root, 'README.rst')
    with codecs.open(readme_filename, encoding='UTF-8') as readme_file:
        lines = [line.rstrip('\n') for line in readme_file]
    lines = lines[4:]
    return "\n".join(lines)


setup(
    name='possible',
    version=find_version("possible", "__init__.py"),
    description='Possible is configuration management tool',
    long_description=long_description(),
    long_description_content_type='text/x-rst',
    keywords=['configuration management'],
    author='Gena Makhomed',
    author_email='makhomed@gmail.com',
    url='https://github.com/makhomed/possible',
    license='GPLv3',
    platforms=['Linux'],
    packages=['possible'],
    include_package_data=True,
    install_requires=['PyYAML>=5.3.1', 'Jinja2>=2.11.2'],
    scripts=['bin/pos'],
    classifiers=[  # https://pypi.org/classifiers/
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration',
    ],
)
