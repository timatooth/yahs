# YaHS Yet another HTTP Server

HTTP server in a single Python file. Offers a Python decorator to register
functions for URL resources using regular expressions we all know and love.*
Handy for trying out your future REST api ideas.

- HTTPS Support.
- Uses Python ```logging``` module.
- Self documenting API index at ```/``` when you use docstrings on the handlers.
- ```/reload``` reloads any module(s) that register any handlers to save stopping/starting server.
- Basic CORS responses enabled.

Probably not better than Django, Flask, Jersey or *other framework* :P

## Installation

Manual Install

```python setup.py install```

## Sample Usage
```
from yahs import Server, Response
@Server.handle('GET', '/food')
def get_food(request):
    """ Simple get food request """
    response = Response()
    response.body = "Hello there, here's some food!"
    return response

@Server.handle('GET', r'/products/(?P<id_yo>[0-9]+)')
def get_product_by_id(request, id_yo):
    """Gets a product by numeric id.
    E.g /products/240
    The regex named group/backreference 'id_yo' will get added to the call when
    someone requests the matching url pattern. It will have the value 240.
    """
    response = Response()
    response.body = "<h1>Yo here it is... Product: #{}</h1>".format(id_yo)
    return response

server = Server()  # default port is 4321
server.start()
```

## License

MIT License

### Do-maybe-list
- Testing -.-
- Support class based Resource decorators with get, post, delete etc methods.

**Results may vary depending on how much you know and love regular expressions.*
