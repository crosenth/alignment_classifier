import classifier
import setuptools
import sys

if sys.version_info < (3, 0):
    raise EnvironmentError('Please install using pip3 or python3')

setuptools.setup(author='Chris Rosenthal',
                 author_email='crosenth@gmail.com',
                 description='Alignment based taxonomic classifier',
                 name='classifier',
                 packages=setuptools.find_packages(exclude=['tests']),
                 entry_points={'console_scripts':
                               {'classifier = classifier:main'}},
                 version=classifier.version(),
                 url='https://github.com/crosenth/alignment_classifier',
                 package_data={'classifier': ['data/*']},
                 install_requires=['pandas>=0.17.1'],
                 license='GPLv3',
                 classifiers=[
                     'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                     'Development Status :: 3 - Alpha',
                     'Environment :: Console',
                     'Operating System :: OS Independent',
                     'Intended Audience :: End Users/Desktop',
                     ('License :: OSI Approved :: '
                      'GNU General Public License v3 (GPLv3)'),
                     'Programming Language :: Python :: 3 :: Only'])
