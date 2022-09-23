from io import BytesIO
from typing import Dict
import re, os

def testLanding(app, client):
    del app
    response = client.get('/')
    assert response.status_code == 200

def testGenerateKey(client):
    response = client.get('/S4/generateKey')
    assert response.status_code == 200
    assert response
    assert response.data is not None;
    # assert len(response.data["Key"]) == 16
    
def testPutObject(client):
    f = open('./InputTetris.png', "rb");
    data = dict(
        file=(BytesIO(f.read()), 'OutputTetris.png')
    )
    
    response = client.put('/S4/PutObject?Key=TestKey', content_type='multipart/form-data', data = data)
    assert response.status_code == 201

# THIS FUNCTION NEEDS TO BE AFTER THE testPutObject test TO WORK.
def testGetObject(client):
    response = client.get('/S4/GetObject?Key=OutputTetris.png', content_type='multipart/form-data')
    assert response.status_code == 200
    
def testListObject(client):
    response = client.get("/S4/ListObjects")
    assert response.status_code == 200