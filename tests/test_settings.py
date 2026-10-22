import base64
import json
import unittest
from unittest.mock import patch
from settings_store import load, save, validate

class SettingsTest(unittest.TestCase):
    def test_roundtrip(self):
        data={'fuel':26.4,'margin':10.0,'mode':'Opslag op inkoop'}
        with patch('settings_store.request',return_value={'content':{'sha':'next'}}) as request:
            self.assertEqual(save('test',data,'old'),'next')
            body=request.call_args.args[2]
            self.assertEqual(body['sha'],'old')
            encoded=body['content']
            self.assertEqual(json.loads(base64.b64decode(encoded)),data)
        with patch('settings_store.request',return_value={'content':encoded,'sha':'next'}):
            self.assertEqual(load('test'),(data,'next'))

    def test_missing(self):
        with patch('settings_store.request',return_value=None):
            self.assertEqual(load('test')[0]['fuel'],0)
        with self.assertRaises(ValueError): save('',{},None)

    def test_invalid(self):
        for data in ({'fuel':float('nan')},{'margin':-1},{'mode':'Marge op verkoop','margin':100}):
            with self.assertRaises(ValueError): validate(data)
