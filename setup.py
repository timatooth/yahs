from distutils.core import setup

setup(
    name='yahs',
    version='1.0',
    # packages=[''],
    package_dir={'': 'src'},
    py_modules=['yahs'],
    keywords = ["http", "rest", "xml"],
    url='https://github.com/timatooth/yahs',
    license='MIT',
    author='Tim Sullivan',
    author_email='tsullivan@timatooth.com',
    download_url='https://github.com/timatooth/yahs/tarball/1.0',
    description='Super basic HTTP server for creating and testing REST APIs',
    classifiers= [
        'Programming Language :: Python'
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries'
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    long_description="""
Yet another HTTP Server (YaHS)
------------------------------

Provides simple decorator API to easily register a Python function as a REST url
handler.

E.g
@Server.handle('GET', '/food')
def get_food(request):
    return "Tasty food"

"""
)
