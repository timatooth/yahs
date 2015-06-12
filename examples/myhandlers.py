from yahs import Server, Response

# Store some data here
mediastore = {}

@Server.handle('GET', '^/food$')
def get_food(request):
    """ Simple get food request """
    return "Hello there, here's some food!"

@Server.handle('GET', '^/cake$')
def get_food(request):
    return "lies!"

@Server.handle('GET', '^/derp$')
def get_food(request):
    pass



@Server.handle('GET', r'/events/(?P<id>[0-9]+)')
def get_by_id(request, id):
    """Get event by ID
    """
    res = Response()
    res.body = "hello id: {}".format(id)
    return res

@Server.handle('POST', r'/events/(?P<id>[a-z]+)/media/?')
def add_file_to_event(request, id):
    """Add a file to an event
    """
    print "Got media file"
    mediastore[id] = request.body
    res = Response()
    res.status_code = 201
    res.status_message = 'Created'
    return res
