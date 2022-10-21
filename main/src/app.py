import secrets, os
import atexit
import json
import time
import requests

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
Key200 = api.model(
    "Key",
    {
        "Key": fields.String(
            description="Newly generated API key",
            example="j4ZRylUaPzz1wv2pahMYBA",
        ),
    },
)

GetObject400 = api.model(
    "GetObject",
    {
        "msg": fields.String(
            example="'Key not specified' or 'No object associated with key'}",
        ),
    },
)

GetObject404 = api.model(
    "GetObject2",
    {
        "msg": fields.String(
            example="Invalid file specified",
        ),
    },
)

GetObject200 = api.model(
    "GetObject3",
    {
        "GetObject": fields.String(
            required=True,
            description="Get an object by the object name (like bject ID or object HASH)",
            example="For now, it's the actual filename, like bob.txt. We will eventually replace filename with the"
            + "object's actual ID/HASH.",
        ),
    },
)

PutObject400 = api.model(
    "PutObject",
    {
        "msg": fields.String(
            example="'Empty filepath' or 'Key not specified' or 'Key not unique'",
        ),
    },
)

PutObject404 = api.model(
    "PutObject2",
    {
        "msg": fields.String(
            example="No file specified",
        ),
    },
)

PutObject201 = api.model(
    "PutObject3",
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
    "ListObjects",
    {
        "msg": fields.String(
            description="Success message",
            example="Files retrieved successfully",
        ),
        "files": fields.String(
            description="List of object names in storage.",
            example="['image.jpeg', 'file.txt', 'test.pdf']",
        ),
    },
)

DeleteObject400 = api.model(
    "Deletebject",
    {
        "Key": fields.String(example="Key not specified"),
    },
)

DeleteObject404 = api.model(
    "Deletebject2",
    {
        "Key": fields.String(example="Key does not exist"),
    },
)

DeleteObject200 = api.model(
    "Deletebject3",
    {
        "Key": fields.String(
            description="Deletes an object store on the local filesystem.",
            example="File deleted successfully",
        ),
    },
)

TIMEOUT = 0.1
FILE_PATH = "../tests"
# FILE_PATH = os.getenv("FILE_PATH")
ALL_WORKERS = [
    "http://127.0.0.1:5001/",
    "http://127.0.0.1:5002/",
    "http://127.0.0.1:5003/",
    "http://127.0.0.1:5004/",
]
healthy_workers = []

key_to_filename = {}  # string to string
key_to_nodes = {}  # string to list[int]
node_to_keys = {}  # int to set[string]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Endpoint parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
key_param = ns.parser()
key_param.add_argument("Key", type=str)

file_param = ns.parser()
file_param.add_argument("file", location="files", type=FileStorage)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Actual endpoints ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ----------------------------------- StartNetwork -----------------------------------
@app.before_first_request
def start():
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
                             params={"workers": healthy_workers}, 
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
@app.before_first_request
def healthCheckWrapper():
    starttime = time.time()
    while True:
        print(healthCheck())
        time.sleep(60.0 - ((time.time() - starttime) % 60.0))
        
    # @ns.doc("HealthCheck")
    # @api.response(200, "Success", model=ListObjects200)

def healthCheck():
    result = ""
    # {"msg": "Not implemented"}, 501
    #result + "stuff"
    return result

    
# ----------------------------------- RecordPutObject -----------------------------------
@ns.route("/RecordPutObject")
@ns.expect(key_param)
class RecordPutObject(Resource):
    @ns.doc("RecordPutObject")
    @api.response(200, "Success", model=GetObject200)
    @api.response(400, "Error: Bad Request", model=GetObject400)
    @api.response(404, "Error: Not Found", model=GetObject404)
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
    @api.response(400, "Error: Bad Request", model=DeleteObject400)
    @api.response(404, "Error: Not Found", model=DeleteObject404)
    def post(self):
        return {"msg": "Not implemented"}, 501


# ----------------------------------- FindObject -----------------------------------
@ns.route("/FindObject")
@ns.expect(key_param)
class deleteObject(Resource):
    @ns.doc("FindObject")
    @api.response(200, "Success", model=DeleteObject200)
    @api.response(400, "Error: Bad Request", model=DeleteObject400)
    @api.response(404, "Error: Not Found", model=DeleteObject404)
    def get(self):
        key = request.json["key"]
        if key in key_to_filename:
            return {"found": True, "filename": key_to_filename[key]}, 200
        else:
            return {"found": False, "filname": None}


# Main
if __name__ == "__main__":
    app.run(debug=True)