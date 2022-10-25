import secrets, os
import atexit
import json
import time
import requests
import math

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
    version="0.0.1",
    title="S4 Main Node",
    description="Super Simple Storage System Main Node",
)

ns = api.namespace("S4", description="S4 API Endpoints")

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
            description="Success message",
            example="Files retrieved successfully",
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
ALL_WORKERS = [ "http://127.0.0.1:5001/",
                "http://127.0.0.1:5002/",
                "http://127.0.0.1:5003/",
                "http://127.0.0.1:5004/",]
healthy_workers = []

key_to_filename = {}  # string to string
key_to_nodes = {}  # string to list[int]
node_to_keys = {}  # int to set[string]

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
@app.before_first_request
def start():
    rt = RepeatedTimer(60, healthCheck);
    
    for worker in ALL_WORKERS:
        try:
            r = requests.get(url=worker + "_joinNetwork", 
                             timeout=TIMEOUT)
            if r.status_code == 200: 
                healthy_workers.append(worker)
        except:
            pass
    for worker in healthy_workers:
        try:
            r = requests.put(url=worker + "_setWorkers", 
                             params={"workers": healthy_workers, "workerIndex": healthy_workers.index(worker)}, 
                             timeout=TIMEOUT)
        except:
            pass

    print(f"******** Launched {len(healthy_workers)} / {len(ALL_WORKERS)} nodes ********")
    
    if len(healthy_workers) == len(ALL_WORKERS):
        return {"msg": "Success"}, 200
    elif len(healthy_workers) > 0:
        return {
            "msg": f"Partial success, launched {len(healthy_workers)} out of {len(ALL_WORKERS)} workers"
        }, 200
    else:
        return {"msg": "Failed to launch worker nodes"}, 500


# ----------------------------------- HealthCheck -----------------------------------
# @app.before_first_request
# def healthCheckWrapper():
#     starttime = time.time()
#     while True:
#         print(healthCheck())
#         time.sleep(60.0 - ((time.time() - starttime) % 60.0)) # currently called once every 60 seconds

def healthCheck():
    result = ""
    healthyWorkers = [] 
    downWorkers = []

    print("HELLO\n\n\n")
    
    # Get the healthy and not healthy workers
    for worker in ALL_WORKERS:
        try:
            r = requests.get(url = worker + "/HealthCheck", timeout = TIMEOUT)
            
            if r.status_code == 200: # success
                healthyWorkers.append(worker)
            elif r.status_code == 503: # server is down/overloaded
                downWorkers.append(worker)
        except:
            pass
        
    # key_to_filename = {}  # string to string
    # key_to_nodes = {}  # string to list[int]
    # node_to_keys = {}  # int to set[string]
    
    forwardingToNode = -1
    
    for downNode in downWorkers: # for each down node
        # get the object that was in this downNode from a node that's up and has a copy of that object
        for key in node_to_keys.get(downWorkers.index(downNode)): # for every file in the down node
            for healthyNode in healthyWorkers: # for every healthy node
                if key in node_to_keys.get(healthyWorkers.index(healthyNode)): # if healthy node has the down node file
                    # Find a healthy node that doesn't have the down node file and is closest to the down node by hash
                    fowardingToNode = findNodeToForwardTo(key, healthyNode, healthyWorkers, downNode)
                    
                    # ??? the worker node only has _forward_object with a filename parameter. Not one that's key + node
                    healthyNode._forward_object(key, forwardingToNode)

def findNodeToForwardTo(key, healthyNode, healthyWorkers, downNode):
    nodeHashValue = math.inf
    forwardingToNode = ""
    
    for forwardToNode in healthyWorkers:
        if key not in node_to_keys.get(healthyWorkers.index(forwardToNode)) and forwardToNode != healthyNode:
            tempHash = nodeHash(ALL_WORKERS.index(forwardToNode), ALL_WORKERS.index(downNode))
            if tempHash < nodeHashValue:
                nodeHashValue = tempHash
                fowardingToNode = forwardToNode
    
    return fowardingToNode

# ??? Should we use the same md5 hashing like the worker node uses, or is a mod fine becuase this is for that grouping 
# thing that we will implement later?
def nodeHash(indexNodeA, indexNodeB):
    # ??? can always change the hash whenever we need to
    return (indexNodeA % 3) - (indexNodeB % 3)

# ----------------------------------- RecordPutObject -----------------------------------
@ns.route("/RecordPutObject")
@ns.expect(key_param)
class RecordPutObject(Resource):
    @ns.doc("RecordPutObject")
    @api.response(200, "Success", model=RecordPutObject200)
    def post(self):
        # TODO check that request comes from worker
        body = request.json
        key, filename, nodes = body["key"], body["filename"], body["nodes"]
        self.key_to_filename[key] = filename
        self.filename_to_nodes[filename] = nodes
        for node in nodes:
            self.node_to_keys[node].add(key)
        return {"msg": "Success"}, 200


# ----------------------------------- ListObjects -----------------------------------
@ns.route("/ListObjects")
class listObjects(Resource):
    @ns.doc("ListObjects")
    @api.response(200, "Success", model=ListObjects200)
    def get(self):
        return {"msg": "Success", "objects": key_to_filename}, 200


# ----------------------------------- DeleteObject -----------------------------------
@ns.route("/DeleteObject")
@ns.expect(key_param)
class deleteObject(Resource):
    @ns.doc("DeleteObject")
    @api.response(200, "Success", model=DeleteObject200)
    @api.response(404, "Error: Not Found", model=DeleteObject404)
    def post(self):
        return {"msg": "Not implemented"}, 501


# ----------------------------------- FindObject -----------------------------------
@ns.route("/FindObject")
@ns.expect(key_param)
class deleteObject(Resource):
    @ns.doc("FindObject")
    @api.response(200, "Success", model=FindObject200)
    @api.response(404, "Error: Not Found", model=FindObject404)
    def get(self):
        key = request.json["key"]
        if key in key_to_filename:
            return {"found": True, "filename": key_to_filename[key]}, 200
        else:
            return {"found": False}, 404
        
# Main
if __name__ == "__main__":
    app.run(debug=True)