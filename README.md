# YaHS Yet another HTTP Server

[![Build Status](https://travis-ci.org/timatooth/yahs.svg?branch=master)](https://travis-ci.org/timatooth/yahs)

HTTP server in a single Python file. Offers a Python decorator to register
functions for URL resources using regular expressions we all know and love.*
Handy for trying out your future REST api ideas.

- Written in a single .py file
- No extra libraries needed
- HTTPS
- Uses Python ```logging``` module
- Self documenting API index at ```/``` when you use docstrings on the handlers.
- ```/yahs/reload``` reloads any module(s) that register any handlers to save stopping/starting server
- Basic Cross-Origin Resource Sharing (CORS) responses enabled for all request types

Probably not better than Django, Flask, Jersey or *other framework* :P

## Installation

Using pip

```pip install yahs```

Manual Install

```python setup.py install```

## Sample Usage
```
from yahs import Server, Response
@Server.handle('GET', '^/food$')
def get_food(request):
    return "Hello there, here's some food!"

@Server.handle('GET', r'/products/(?P<product_id>[0-9]+)')
def get_product_by_id(request, product_id):
    """Gets a product by numeric id.
    E.g /products/240
    The regex named group/backreference 'product_id' will get added to the call when
    someone requests the matching url pattern. It will have the value 240.
    """
    response = Response()
    response.body = "<h1>Yo here it is... Product: #{}</h1>".format(product_id)
    return response

server = Server()  # default port is 4321
server.start()
server.wait()  # blocks the program from exiting early
```

## License

MIT License

### Do-maybe-list
- Support class based Resource decorators with get, post, delete etc methods.

**Results may vary depending on how much you know and love regular expressions.*
