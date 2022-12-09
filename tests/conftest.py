import pytest
import sys
import json
import threading
from werkzeug.serving import make_server
import requests
from multiprocessing import Process

from worker.app import app as worker_app
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
                    "testing" : True
                })

    yield main_url
