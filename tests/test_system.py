import pytest
import requests
from io import BytesIO
import sys
import json
sys.path.append("../tests")

# #Perform Health Check
def test_health_check(start_server):
    """ Tests HealthCheck endpoint for all workers """
    worker_1 = requests.get("http://127.0.0.1:5001/HealthCheck", timeout=5)
    worker_2 = requests.get("http://127.0.0.1:5002/HealthCheck", timeout=5)
    worker_3 = requests.get("http://127.0.0.1:5003/HealthCheck", timeout=5)


    assert worker_1.status_code == 200
    assert worker_2.status_code == 200
    assert worker_3.status_code == 200

def test_put_delete_object(start_server):
    """ Test PutObject and DeleteObject endpoints """
    put_res = put_tetris_obj()
    assert put_res.status_code == 201

    del_res = delete_tetris_obj()
    assert del_res.status_code == 200

def test_get_delete_object(start_server):
    """ Test PutObject, GetObject, and DeleteObject endpoints """
    put_res = put_hello_world_obj()
    assert put_res.status_code == 201

    get_res = requests.get("http://127.0.0.1:5002/GetObject", params={"key":"hello_output"})
    assert get_res.status_code == 200

    delete_res = delete_hello_world_obj()
    assert delete_res.status_code == 200

def test_delete_object(start_server):
    """ Test PutObject and DeleteObject endpoints """
    put_res = put_hello_world_obj()
    assert put_res.status_code == 201

    del_res = delete_hello_world_obj()
    assert del_res.status_code == 200

def test_list_objects(start_server):
    """ Test ListObject endpoints """
    put_hello_world_obj()
    put_tetris_obj()
    list_res = requests.get("http://127.0.0.1:5001/ListObjects")

    assert list_res.status_code == 200
    output = json.loads(list_res.text)["keysToFilenames"]

    assert "OutputTetris" in output
    assert output["OutputTetris"] == "InputTetris.png"
    assert "hello_output" in output
    assert output["hello_output"] == "HelloWorld.txt"

    del_res_1 = delete_tetris_obj()
    del_res_2 = delete_hello_world_obj()
    assert del_res_1.status_code == 200
    assert del_res_2.status_code == 200

def put_tetris_obj():
    """ Performs PutObject on a worker node with image file"""
    file = open("./InputTetris.png", "rb")
    file.seek(0)
    worker_1 = requests.put("http://127.0.0.1:5001/PutObject", files={"file" : file}, params={"key":"OutputTetris"})
    return worker_1

def put_hello_world_obj():
    """ Performs PutObject on a worker node with txt file"""
    file = open("./HelloWorld.txt", "rb")
    file.seek(0)
    worker_1 = requests.put("http://127.0.0.1:5001/PutObject", files={"file" : file}, params={"key":"hello_output"})
    return worker_1

def delete_hello_world_obj():
    """ Performs DeleteObject on a worker node for txt file"""
    worker_1 = requests.put("http://127.0.0.1:5002/DeleteObject", params={"key":"hello_output"})
    print("Status_code for delete: " , worker_1.status_code)
    return worker_1

def delete_tetris_obj():
    """ Performs DeleteObject on a worker node for img file"""
    worker_1 = requests.put("http://127.0.0.1:5002/DeleteObject", params={"key":"OutputTetris"})
    print("Status_code for delete: " , worker_1.status_code)
    return worker_1
