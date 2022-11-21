import pytest
import sys
import json
import threading
from werkzeug.serving import make_server
import requests

from worker.app import app as worker_app
from main.src.app import app as main_app

class ServerThread(threading.Thread):

    def __init__(self, app, port):
        threading.Thread.__init__(self)
        self.server = make_server("127.0.0.1", port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print('starting server')
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

@pytest.fixture(scope='session', autouse=True)
def start_server():
    global main_node
    #Start up three workers

    ports = [5001, 5002, 5003]
    workers = []
    for i in range(len(ports)):
        worker = ServerThread(worker_app, ports[i])
        worker.start()
        workers.append(worker)

    #Start up a main node
    main_url = "http://127.0.0.1:5000/"
    main_node = ServerThread(main_app, 5000)
    main_node.start()

    #Set up worker nodes
    ALL_WORKERS = ["http://127.0.0.1:" + str(port) + "/" for port in ports]
    for i in range(len(ports)):
        url = "http://127.0.0.1:" + str(ports[i]) + "/_SetWorkers"
        res = requests.put(url, params={
                    "workers": json.dumps(ALL_WORKERS),
                    "workerIndex": i,
                    "mainUrl": main_url,
                    "testing" : True
                })

    print('server started')
    yield main_node
    main_node.shutdown()
    for worker in workers:
        worker.shutdown()
