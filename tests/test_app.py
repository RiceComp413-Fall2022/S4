from io import BytesIO
from typing import Dict
import pytest, json


@pytest.fixture(autouse=True)
def do_not_mutate_keys_json():
    # save keys.json before modification
    with open("../keys.json", "r") as f:
        keys_to_files = json.load(f)

    # test will be run here
    yield 

    # restore keys.json to original state
    with open("../keys.json", "w") as f:
        f.write(json.dumps(keys_to_files))

def test_landing(app, client):
    del app
    response = client.get("/")
    assert response.status_code == 200


def test_generate_key(client):
    response = client.get("/S4/GenerateKey")
    assert response.status_code == 200
    assert response
    assert response.data is not None
    # assert len(response.data["Key"]) == 16


def test_put_object(client):
    f = open("./InputTetris.png", "rb")
    data = dict(file=(BytesIO(f.read()), "OutputTetris.png"))

    response = client.put(
        "/S4/PutObject?Key=TestKey", content_type="multipart/form-data", data=data
    )
    assert response.status_code == 201


def test_put_duplicate_key(client):
    f = open("./InputTetris.png", "rb")
    data = dict(file=(BytesIO(f.read()), "OutputTetris.png"))

    first_response = client.put(
        "/S4/PutObject?Key=TestKey", content_type="multipart/form-data", data=data
    )
    assert first_response.status_code == 201

    data = dict(file=(BytesIO(f.read()), "OutputTetris.png"))
    second_response = client.put(
        "/S4/PutObject?Key=TestKey", content_type="multipart/form-data", data=data
    )
    assert second_response.status_code == 400
    assert second_response.json["msg"] == "Key not unique"


def test_get_object(client):
    f = open("./InputTetris.png", "rb")
    data = dict(file=(BytesIO(f.read()), "OutputTetris.png"))
    put_response = client.put(
        "/S4/PutObject?Key=TestKey", content_type="multipart/form-data", data=data
    )
    assert put_response.status_code == 201

    get_response = client.get(
        "/S4/GetObject?Key=TestKey", content_type="multipart/form-data"
    )
    assert get_response.status_code == 200
    # TODO test that the object we get back is the same as the object we sent


def test_list_objects(client):
    response = client.get("/S4/ListObjects")
    assert response.status_code == 200
    # TODO flesh this out
