import pytest
import json
from werkzeug.serving import make_server
import requests
import sys

sys.path.insert(0, '../worker/')
from worker.security import internal_required, api_required, INTERNAL_HEADERS
from worker.app import app as worker_app

sys.path.insert(0, '../main/src/')
from main.src.app import app as main_app

@pytest.fixture(scope='session', autouse=True)
def start_server():
    global main_node
    #Start up three workers

    ports = [5001, 5002, 5003]

    #Start up a main node
    main_url = "http://127.0.0.1:5000/"

    ALL_WORKERS = ["http://127.0.0.1:" + str(port) + "/" for port in ports]
    for i in range(len(ports)):
        url = "http://127.0.0.1:" + str(ports[i]) + "/_SetWorkers"
        res = requests.put(url, params={
                    "workers": json.dumps(ALL_WORKERS),
                    "workerIndex": i,
                    "mainUrl": main_url,
                    "testing" : True},
                headers=INTERNAL_HEADERS)

    yield main_url
