from io import BytesIO
import math
from platform import node
import time
import json
import atexit
import requests
import secrets, os
from collections import defaultdict
import socket

from time import sleep
from datetime import datetime
from threading import Timer

from flask import Flask, request, flash, send_file, jsonify
from flask_restx import Api, Resource, fields

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from security import internal_required, admin_required, INTERNAL_KEY

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

authorizations = {"apikey": {"type": "apiKey", "in": "header", "name": "X-API-KEY"}}

api = Api(
    app,
    version="0.0.2",
    title="S4 Main Node",
    description="Super Simple Storage System Main Node",
    authorizations=authorizations,
    security="apikey",
)

ns = api.namespace("", description="S4 API Endpoints")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ API Model for example header/body and the response ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ScaleUp200 = api.model(
    "ScaleUp Success",
    {
        "msg": fields.String(
            required=True,
            description="Doubles the number of nodes in the system",
            example="Success",
        ),
    },
)

ScaleUp400 = api.model(
    "ScaleUp Failure",
    {
        "msg": fields.String(
            required=True,
            description="Doubles the number of nodes in the system",
            example="Needs X healthy nodes",
        ),
    },
)

ScaleDown200 = api.model(
    "ScaleDown Success",
    {
        "msg": fields.String(
            required=True,
            description="Halves the number of nodes in the system",
            example="Success",
        ),
        "nodes": fields.String(
            description="List of nodes that were cleared.",
            example='{"http://127.0.0.1:5001/", "http://127.0.0.1:5002/", "http://127.0.0.1:5003/"}',
        ),
    },
)

ScaleDown400 = api.model(
    "ScaleDown Failure",
    {
        "msg": fields.String(
            required=True,
            description="Halves the number of nodes in the system",
            example="Needs X healthy nodes",
        ),
    },
)


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

TIMEOUT = 10
PORT_NUM = 8080
# FILE_PATH = os.getenv("PORT_NUM")

key_to_filename = {}  # string to string
key_to_nodes = {}  # string to list[string]
node_to_keys = defaultdict(set)  # string to set[string]

processed_down_nodes = set()

hostname = socket.gethostname()
ipAddr = socket.gethostbyname(hostname)
main_url = f"http://{ipAddr}:{PORT_NUM}/"
# main_url = "http://127.0.0.1:5000/"

internal_headers = {"X-Api-Key": INTERNAL_KEY}

healthy_workers = []

# ALL_WORKERS = ["http://127.0.0.1:5001/", "http://127.0.0.1:5002/", "http://127.0.0.1:5003/", "http://127.0.0.1:5004/", "http://127.0.0.1:5005/", "http://127.0.0.1:5006/"]
with open("nodes.txt") as f:
    url_list = f.readlines()
ALL_WORKERS = [url.strip() for url in url_list]
print(ALL_WORKERS)

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

arr_param = ns.parser()
arr_param.add_argument("nodes", type=str, action="append")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Actual endpoints ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ----------------------------------- StartNetwork -----------------------------------

# YOU MUST RESTART LOCALHOST FOR THIS START TO RUN. IF LOCALHOST IS ALREADY OPEN ON YOUR BROWSER WHEN YOU TYPE FLASK RUN,
# NO REQUEST WILL BE MADE AND SO THIS FUNCTION CAN'T CALL BEFORE A REQUEST IF NO REQUEST IS MADE.
@app.before_first_request
def start():
    rt = RepeatedTimer(10, healthCheck)

    for worker in ALL_WORKERS:
        try:
            r = requests.get(
                url=worker + "_JoinNetwork", timeout=TIMEOUT, headers=internal_headers
            )
            if r.status_code == 200:
                healthy_workers.append(worker)
        except:
            pass

    for idx, worker in enumerate(healthy_workers):
        try:
            r = requests.put(
                url=worker + "_SetWorkers",
                params={
                    "workers": json.dumps(ALL_WORKERS),
                    "workerIndex": idx,
                    "mainUrl": main_url,
                },
                timeout=TIMEOUT,
                headers=internal_headers,
            )
        except:
            pass

    print(
        f"\n\n-------------- Running {len(healthy_workers)} / {len(ALL_WORKERS)} nodes --------------\n\n"
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

    global ALL_WORKERS
    global node_to_keys
    global key_to_nodes
    global key_to_filename
    global processed_down_nodes

    # FOR TESTING PURPOSES
    for key, value in node_to_keys.items():
        print("node " + key + "\nkey " + str(value))

    # Get the healthy and not healthy workers
    for worker in ALL_WORKERS:
        try:
            r = requests.get(url=worker + "/HealthCheck", headers=internal_headers)
            if r.status_code == 200:
                healthyWorkers.append(worker)
            else:  # server is down/overloaded
                downWorkers.append(worker)
        except:
            downWorkers.append(worker)

    now = datetime.now()
    dt_string = now.strftime("%H:%M:%S")

    if len(downWorkers) == 0:
        print("\nAll nodes are \U0001f600healthy\U0001f600 at " + dt_string + "\n")

    # for each down node
    for downNode in downWorkers:
        if downNode in processed_down_nodes:
            continue
        processed_down_nodes.add(downNode)
        print("\nNode " + downNode + " is \U00002757down!\U00002757\n")

        # get the object that was in this downNode from a node that's up and has a copy of that object
        for key in node_to_keys[downNode]:  # for every file in the down node
            start_node_idx = ALL_WORKERS.index(downNode)  # start at the down node

            contains_url = ""

            # iterate through all nodes (including looping) to get a node with the file of that down node,
            # but don't loop back to the down node
            for i in range(start_node_idx + 1, start_node_idx + len(ALL_WORKERS)):
                node_idx = i % len(ALL_WORKERS)
                node_url = ALL_WORKERS[node_idx]

                if key in node_to_keys[node_url] and node_url in healthyWorkers:
                    contains_url = node_url

            if contains_url == "":
                print(
                    "\U00002757\U00002757\U00002757ALL NODES ARE DOWN!!!\U00002757\U00002757\U00002757\n"
                )
                return

            # forward to all nodes, break on the first successful request
            for i in range(start_node_idx + 1, start_node_idx + len(ALL_WORKERS)):
                node_idx = i % len(ALL_WORKERS)
                node_url = ALL_WORKERS[node_idx]

                if key not in node_to_keys[node_url]:
                    try:
                        r = jsonify(
                            requests.put(
                                contains_url + "/_ForwardObject",
                                params={"key": key, "forwardingToNode": node_url},
                                headers=internal_headers,
                            )
                        )

                        if r.status_code == 200:
                            node_to_keys[node_url].add(key)
                            key_to_nodes[key].append(node_url)
                            break
                    except:
                        pass


# ----------------------------------- Scale Down -----------------------------------
@ns.route("/ScaleDown")
class ScaleDown(Resource):
    @ns.doc("ScaleDown")
    @api.response(200, "Success", model=ScaleDown200)
    @api.response(400, "Failure", model=ScaleDown400)
    @admin_required
    def post(self):
        global ALL_WORKERS
        global node_to_keys
        global key_to_nodes
        global key_to_filename
        global processed_down_nodes

        if len(ALL_WORKERS) <= 3:
            return {"msg": "Must have at least 2 workers running"}, 400

        workers_to_remove = ALL_WORKERS[(len(ALL_WORKERS) // 2) :]
        ALL_WORKERS = ALL_WORKERS[: (len(ALL_WORKERS) // 2)]

        res = redistribute_files()
        if not res:
            return {"msg": "Error redistributing all files"}, 400

        return {
            "msg": f"Successfully cleared nodes",
            "nodes": f"{json.dumps(workers_to_remove)}",
        }, 200


# ----------------------------------- DoubleWorkers -----------------------------------
@ns.route("/ScaleUp")
@ns.expect(arr_param)
class ScaleUp(Resource):
    @ns.doc("ScaleUp")
    @api.response(200, "Success", model=ScaleUp200)
    @api.response(400, "Failure", model=ScaleUp400)
    @admin_required
    def post(self):
        global ALL_WORKERS
        global node_to_keys
        global key_to_nodes
        global key_to_filename
        global processed_down_nodes
        new_nodes = json.loads(request.form["nodes"])
        nodes_to_add = []
        for worker in new_nodes:
            try:
                r = requests.get(
                    url=worker + "_JoinNetwork",
                    timeout=TIMEOUT,
                    headers=internal_headers,
                )
                if r.status_code == 200:
                    nodes_to_add.append(worker)
            except:
                pass
        if len(nodes_to_add) < len(ALL_WORKERS):
            return {"msg": f"Needs at least {len(ALL_WORKERS)} healthy nodes"}, 400
        ALL_WORKERS += nodes_to_add

        redistribute_files()

        return {"msg": "Success"}, 200


def redistribute_files():
    for idx, worker in enumerate(ALL_WORKERS):
        try:
            r = requests.put(
                url=worker + "_SetWorkers",
                params={
                    "workers": json.dumps(ALL_WORKERS),
                    "workerIndex": idx,
                    "mainUrl": main_url,
                },
                timeout=TIMEOUT,
                headers=internal_headers,
            )
        except:
            pass

    # Redistribute files
    redistribute_all = True
    for key in key_to_nodes:
        nodes = set(key_to_nodes[key])
        del key_to_nodes[key]
        file = None
        # Get the file
        for node in nodes:
            try:
                r = requests.get(
                    node + "_GetObject",
                    params={"key": key, "filename": key_to_filename[key]},
                    stream=True,
                    headers=internal_headers,
                )
                if r.status_code == 200:
                    file = BytesIO(r.content)
                    break
            except:
                pass

        # Put the file again
        if file == None:
            continue
        file.seek(0)
        f = file.read()
        put = False
        for node in ALL_WORKERS:
            try:
                r = requests.put(
                    node + "PutObject",
                    params={"key": key, "filename": key_to_filename[key]},
                    files={"file": f},
                    headers=internal_headers,
                )
                if r.status_code == 201:
                    print(f"put on node {node}")
                    put = True
                    break
            except:
                pass

        if not put:
            key_to_nodes[key] = nodes
            redistribute_all = False
            continue

        # Delete the file from old nodes
        for node in nodes:
            if node in key_to_nodes[key]:
                continue
            try:
                r = requests.put(
                    url=node + "/_DeleteObject",
                    params={"key": key},
                    timeout=TIMEOUT,
                    headers=internal_headers,
                )
                node_to_keys[node].remove(key)
            except:
                pass
    return redistribute_all


@ns.route("/HealthCheck")
class HealthCheck(Resource):
    def get(self):
        return {"msg": "Success"}, 200


# ----------------------------------- RecordPutObject -----------------------------------
@ns.route("/RecordPutObject")
@ns.expect(key_param)
class RecordPutObject(Resource):
    @ns.doc("RecordPutObject")
    @api.response(200, "Success", model=RecordPutObject200)
    @internal_required
    def post(self):
        global node_to_keys
        global key_to_nodes
        global key_to_filename

        # TODO check that request comes from worker
        body = request.form
        key, filename, nodes = body["key"], body["filename"], json.loads(body["nodes"])

        key_to_filename[key] = filename
        key_to_nodes[key] = nodes

        for node in nodes:
            node_to_keys[node].add(key)

        return {"msg": "Success"}, 200


# ----------------------------------- ListObjects -----------------------------------
@ns.route("/ListObjects")
class listObjects(Resource):
    @ns.doc("ListObjects")
    @api.response(200, "Success", model=ListObjects200)
    @internal_required
    def get(self):
        print(request.origin)
        global key_to_filename

        return {"msg": "Success", "objects": json.dumps(key_to_filename)}, 200


# ----------------------------------- DeleteObject -----------------------------------
@ns.route("/DeleteObject")
@ns.expect(key_param)
class deleteObject(Resource):
    @ns.doc("DeleteObject")
    @api.response(200, "Success", model=DeleteObject200)
    @api.response(404, "Error: Not Found", model=DeleteObject404)
    @internal_required
    def post(self):
        healthyWorkers = []
        args = request.args
        key = args.get("key")

        global ALL_WORKERS
        global node_to_keys
        global key_to_nodes
        global key_to_filename

        if key not in key_to_filename:
            return {"msg": "file not found"}, 400

        for worker in ALL_WORKERS:
            try:
                r = requests.get(
                    url=worker + "/HealthCheck",
                    timeout=TIMEOUT,
                    headers=internal_headers,
                )

                if r.status_code == 200:  # success
                    healthyWorkers.append(worker)
            except:
                pass

        # print(dict(node_to_keys))
        # print(healthyWorkers, key_to_nodes, key_to_nodes[key])

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
                        headers=internal_headers,
                    )

                    if r.status_code != 200:
                        return {"msg": "internal server error"}, 500
                except:
                    pass

        for node in key_to_nodes[key]:
            node_to_keys[node].remove(key)

        key_to_filename.pop(key, None)
        key_to_nodes.pop(key, None)

        return {"msg": "Success"}, 200


# ----------------------------------- FindObject -----------------------------------
@ns.route("/FindObject")
@ns.expect(key_param)
class findObject(Resource):
    @ns.doc("FindObject")
    @api.response(200, "Success", model=FindObject200)
    @api.response(404, "Error: Not Found", model=FindObject404)
    @internal_required
    def get(self):
        args = request.args
        key = args.get("key")

        global node_to_keys
        global key_to_nodes
        global key_to_filename

        if key in key_to_nodes:
            return {"found": True, "filename": key_to_filename[key]}, 200
        else:
            return {"found": False}, 404


# Main
if __name__ == "__main__":
    app.run(debug=True)
