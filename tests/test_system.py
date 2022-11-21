import requests
from io import BytesIO
import sys
import json
sys.path.append("../tests")

#Perform Health Check
def test_health_check(start_server):
    worker_1 = requests.get("http://127.0.0.1:5001/HealthCheck", timeout=5)
    worker_2 = requests.get("http://127.0.0.1:5002/HealthCheck", timeout=5)
    worker_3 = requests.get("http://127.0.0.1:5003/HealthCheck", timeout=5)

    assert worker_1.status_code == 200
    assert worker_2.status_code == 200
    assert worker_3.status_code == 200

def test_put_object(start_server):

    file = open("./InputTetris.png", "rb")
    file.seek(0)
    worker_1 = requests.put("http://127.0.0.1:5001/PutObject", files={"file" : file}, params={"key":"OutputTetris"})
    print(worker_1.content)
    assert worker_1.status_code == 201


# def test_get_object(start_server):
#     worker_1 = requests.get("http://127.0.0.1:5001/HealthCheck", timeout=5)
#     worker_2 = requests.get("http://127.0.0.1:5002/HealthCheck", timeout=5)
#     worker_3 = requests.get("http://127.0.0.1:5003/HealthCheck", timeout=5)

#     assert worker_1.status_code == 200
#     assert worker_2.status_code == 200
#     assert worker_3.status_code == 200


# def test_list_objects(start_server):
#     worker_1 = requests.get("http://127.0.0.1:5001/HealthCheck", timeout=5)
#     worker_2 = requests.get("http://127.0.0.1:5002/HealthCheck", timeout=5)
#     worker_3 = requests.get("http://127.0.0.1:5003/HealthCheck", timeout=5)

#     assert worker_1.status_code == 200
#     assert worker_2.status_code == 200
#     assert worker_3.status_code == 200

#cleanup: terminate all instances