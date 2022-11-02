import math
from platform import node
import time
import json
import atexit
import requests
import secrets, os
from collections import defaultdict

from time import sleep
from threading import Timer

from flask import Flask, request, flash, send_file
from flask_restx import Api, Resource, fields

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

api = Api(
    app,
    version="0.0.2",
    title="S4 Main Node",
    description="Super Simple Storage System Main Node",
)

ns = api.namespace("", description="S4 API Endpoints")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ API Model for example header/body and the response ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
RecordPutObject200 = api.model(
    "RecordPutObject Success",
    {
        "msg": fields.String(
            required=True,
            description="Puts an object into the specified filepath (for now). Currently, the object is "
            + "placed somewhere on your local filesystem.",
            example="File successfully saved",
        ),
    },
)

ListObjects200 = api.model(
    "ListObjects Success",
    {
        "msg": fields.String(
            description="Success message", example="Files retrieved successfully"
        ),
        "files": fields.String(
            description="List of object names in storage.",
            example="{'key1': 'image.jpeg', 'key2': 'file.txt', 'key3': 'test.pdf'}",
        ),
    },
)

DeleteObject200 = api.model(
    "DeleteObject Success",
    {
        "msg": fields.String(
            description="Deletes an object store on the local filesystem.",
            example="File deleted successfully",
        ),
    },
)
DeleteObject404 = api.model(
    "DeleteObject Key Not Found",
    {
        "msg": fields.String(example="Key does not exist"),
    },
)

FindObject200 = api.model(
    "FindObject Success",
    {
        "found": fields.String(example="true"),
        "filename": fields.String(example="file.txt"),
    },
)

FindObject404 = api.model(
    "FindObject Key Not Found",
    {
        "found": fields.String(example="false"),
    },
)

TIMEOUT = 0.1
FILE_PATH = "../tests"
# FILE_PATH = os.getenv("FILE_PATH")

key_to_filename = {}  # string to string
key_to_nodes = {}  # string to list[string]
node_to_keys = defaultdict(set)  # string to set[string]

healthy_workers = []
ALL_WORKERS = [
    "http://127.0.0.1:5001/",
    "http://127.0.0.1:5002/",
    "http://127.0.0.1:5003/",
]

# Repeated timer
class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self.run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Endpoint parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
key_param = ns.parser()
key_param.add_argument("Key", type=str)

file_param = ns.parser()
file_param.add_argument("file", location="files", type=FileStorage)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Actual endpoints ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ----------------------------------- StartNetwork -----------------------------------

# ??? THERE IS A SLIGHT PROBLEM!!! YOU MUST RESTART LOCALHOST FOR THIS START TO RUN. IF LOCALHOST IS ALREADY OPEN ON UR
# BROWSER WHEN YOU DO FLASK RUN, NO REQUEST WILL BE MADE AND SO THIS FUNCTION CAN'T CALL BEFORE A REQUEST IF NO
# REQUEST IS MADE.
@app.before_first_request
def start():
    rt = RepeatedTimer(30, healthCheck)

    for worker in ALL_WORKERS:
        try:
            r = requests.get(url=worker + "_JoinNetwork", timeout=TIMEOUT)
            if r.status_code == 200:
                healthy_workers.append(worker)
        except:
            pass
    for idx, worker in enumerate(healthy_workers):
        try:
            r = requests.put(
                url=worker + "_SetWorkers",
                params={"workers": json.dumps(ALL_WORKERS), "workerIndex": idx},
                timeout=TIMEOUT,
            )
        except:
            pass

    print(
        f"******** Launched {len(healthy_workers)} / {len(ALL_WORKERS)} nodes ********"
    )

    if len(healthy_workers) == len(ALL_WORKERS):
        return {"msg": "Success"}, 200
    elif len(healthy_workers) > 0:
        return {
            "msg": f"Partial success, launched {len(healthy_workers)} out of {len(ALL_WORKERS)} workers"
        }, 200
    else:
        return {"msg": "Failed to launch worker nodes"}, 500


# ----------------------------------- HealthCheck -----------------------------------
def healthCheck():
    downWorkers = []
    healthyWorkers = []

    # Get the healthy and not healthy workers
    for worker in ALL_WORKERS:
        try:
            r = requests.get(url=worker + "/HealthCheck", timeout=TIMEOUT)
            if r.status_code == 200:
                healthyWorkers.append(worker)
            else:  # server is down/overloaded
                downWorkers.append(worker)
        except:
            downWorkers.append(worker)

    if len(downWorkers) == 0:
        print("All nodes are healthy!\n")

    # for each down node
    for downNode in downWorkers:
        print("Node " + downNode + " is down.\n")

        # get the object that was in this downNode from a node that's up and has a copy of that object
        for key in node_to_keys.get(downNode):  # for every file in the down node
            start_node_idx = ALL_WORKERS.index(downNode)  # start at the down node

            contains_url = ""
            # iterate through all nodes (including looping) to get a node with the file of that down node,
            # but don't loop back to the down node
            for i in range(start_node_idx + 1, start_node_idx + len(ALL_WORKERS)):
                node_idx = i % len(ALL_WORKERS)
                node_url = ALL_WORKERS[node_idx]
                if key in node_to_keys.get(node_url) and node_url in healthyWorkers:
                    contains_url = node_url

            if contains_url == "":
                print("ALL NODES ARE DOWN!!! \n")
                return

            # forward to all nodes, break on the first successful request
            for i in range(start_node_idx + 1, start_node_idx + len(ALL_WORKERS)):
                node_idx = i % len(ALL_WORKERS)
                node_url = ALL_WORKERS[node_idx]
                if key not in node_to_keys.get(node_url):
                    try:
                        r = requests.put(
                            contains_url + "/_ForwardObject",
                            params={"key": key, "forwardingToNode": node_url},
                        )

                        if r.status_code == 201:
                            break
                    except:
                        pass


# ----------------------------------- RecordPutObject -----------------------------------
@ns.route("/RecordPutObject")
@ns.expect(key_param)
class RecordPutObject(Resource):
    @ns.doc("RecordPutObject")
    @api.response(200, "Success", model=RecordPutObject200)
    def post(self):
        # TODO check that request comes from worker
        body = request.form
        key, filename, nodes = body["key"], body["filename"], json.loads(body["nodes"])

        key_to_filename[key] = filename
        key_to_nodes[key] = nodes
        print(node_to_keys, nodes)
        for node in nodes:
            node_to_keys[node].add(key)
        return {"msg": "Success"}, 200


# ----------------------------------- ListObjects -----------------------------------
@ns.route("/ListObjects")
class listObjects(Resource):
    @ns.doc("ListObjects")
    @api.response(200, "Success", model=ListObjects200)
    def get(self):
        return {"msg": "Success", "objects": json.dumps(key_to_filename)}, 200


# ----------------------------------- DeleteObject -----------------------------------
@ns.route("/DeleteObject")
@ns.expect(key_param)
class deleteObject(Resource):
    @ns.doc("DeleteObject")
    @api.response(200, "Success", model=DeleteObject200)
    @api.response(404, "Error: Not Found", model=DeleteObject404)
    def post(self):
        healthyWorkers = []
        args = request.args
        key = args.get("key")
        if key not in key_to_filename:
            return {"msg": "file not found"}, 400

        for worker in ALL_WORKERS:
            try:
                r = requests.get(url=worker + "/HealthCheck", timeout=TIMEOUT)

                if r.status_code == 200:  # success
                    healthyWorkers.append(worker)
            except:
                pass

        print(healthyWorkers, key_to_nodes, key_to_nodes[key])
        # for each node that holds this key
        for node in key_to_nodes[key]:
            # if the node is a healthy node
            if node in healthyWorkers:

                # try to call the healthy node's _DeleteObject function
                try:
                    r = requests.put(
                        url=node + "/_DeleteObject",
                        params={"key": key},
                        timeout=TIMEOUT,
                    )

                    if r.status_code != 200:
                        return {"msg": "internal server error"}, 500
                except:
                    pass

        key_to_filename.pop(key, None)
        key_to_nodes.pop(key, None)

        for node in node_to_keys:
            node_to_keys[node].remove(key)

        return {"msg": "Success"}, 200


# ----------------------------------- FindObject -----------------------------------
@ns.route("/FindObject")
@ns.expect(key_param)
class findObject(Resource):
    @ns.doc("FindObject")
    @api.response(200, "Success", model=FindObject200)
    @api.response(404, "Error: Not Found", model=FindObject404)
    def get(self):
        args = request.args
        key = args.get("key")
        if key in key_to_filename:
            return {"found": True, "filename": key_to_filename[key]}, 200
        else:
            return {"found": False}, 404


# Main
if __name__ == "__main__":
    app.run(debug=True)
