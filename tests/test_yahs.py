__author__ = 'Tim Sullivan'
import unittest
from yahs import Server

class TestYAHS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print "Setting up YAHS server..."
        server = Server()
        server.start()

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

