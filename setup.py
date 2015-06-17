from setuptools import setup

setup(
    name='yahs',
    version='1.1',
    # packages=[''],
    package_dir={'': 'src'},
    py_modules=['yahs'],
    keywords = ["http", "rest", "json", "decorator"],
    url='https://github.com/timatooth/yahs',
    license='MIT',
    author='Tim Sullivan',
    author_email='tsullivan@timatooth.com',
    download_url='https://github.com/timatooth/yahs/tarball/1.0',
    description='Super basic HTTP server for creating and testing REST APIs',
    tests_require=['requests'],
    test_suite='tests',
    classifiers= [
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    long_description=open('README.rst').read()
)
