__author__ = 'Tim Sullivan'

import unittest
import logging
import json
import random
import requests

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)

from yahs import Server, Response

products = ['apple', 'cake', 'tree', 'fish']
media = {}

class TestYAHS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print "Starting up YAHS server for testing..."
        server = Server()
        server.start()

    def test_get_products(self):
        res = requests.get("http://localhost:4321/products/")
        self.assertEqual(200, res.status_code, "Expects status code 200")

    def test_post_product(self):
        new_product = 'mac'
        res = requests.post("http://localhost:4321/products/", new_product)
        self.assertEqual(200, res.status_code, "Expects status code 200")

        res_check = requests.get("http://localhost:4321/products/")
        self.assertEqual(json.dumps(products), json.dumps(res_check.json()), "response should contain new item + others")

    def test_add_media(self):
        size = 4000
        data = ""
        for b in xrange(size):
            data += chr(random.randint(32, 127))

        res = requests.post('http://localhost:4321/media/textjunk', data)
        self.assertEqual(204, res.status_code, "result after post media file should be 204 no content")

    def test_add_large_media(self):
        size = 1024 * 100
        data = ""
        print "spinning random..."
        for b in xrange(size):
            data += chr(random.randint(32, 127))
        print "spun random"

        res = requests.post('http://localhost:4321/media/textjunk', data)
        self.assertEqual(204, res.status_code, "result after post media file should be 204 no content")

@Server.handle('GET', r'^/products/$')
def get_products(request):
    response = Response()
    response.headers['Content-Type'] = 'application/json'
    response.body = json.dumps(products)
    return response

@Server.handle('POST', r'^/products/$')
def get_products(request):
    products.append(request.body)

    response = Response()
    response.headers['Content-Type'] = 'application/json'
    response.body = json.dumps(products)
    return response

@Server.handle('POST', r'/media/(?P<name>[a-z]+)/?')
def add_media(request, name):
    media[name] = request.body

@Server.handle('GET', r'/media/(?P<name>[a-z]+)/?')
def add_media(request, name):
    response = Response()
    response.headers['Content-Type'] = 'text/plain'
    response.body = media[name]
    return response
