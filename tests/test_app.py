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
    assert response
    assert response.data is not None;
    # assert len(response.data["Key"]) == 16
    
def test_putFile(client):
    f = open('/Users/ericy/Documents/Miscellaneous/Standing.png', "rb");
    data = dict(
        file=(BytesIO(f.read()), 'Standing.png')
    )
    
    response = client.put('/S4/PutObject', content_type='multipart/form-data', data = data)
    assert response.status_code == 201

def test_listFiles(client):
    response = client.get("/S4/ListObjects")
    assert response.status_code == 200
                                        
def test_one():
    assert 1