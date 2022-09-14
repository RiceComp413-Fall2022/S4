from io import BytesIO
from typing import Dict
import re, os


def test_landing(app, client):
    del app
    response = client.get('/')
    assert response.status_code == 200

def test_generateKey(client):
    response = client.get('/S4/generateKey')
    assert response.status_code == 200
    assert response.data is not None;   # definitely need a better assertion here. I tried fiddling with
                                        # regex but I couldn't find any documentation on WrapperTestResponse so 
                                        # it was really annoying to get the right functions.
    
def test_putFile(client):
    data = dict(
        file=(BytesIO(b'blah blah blah'), os.path.join('/Users/ericy/Documents/Photography/Astrophotography', 'Stargazing.jpeg'))
    )
    
    response = client.put('/S4/putFile', content_type='multipart/form-data', data = data)
    assert response.status_code == 201
                                        
def test_one():
    assert 1