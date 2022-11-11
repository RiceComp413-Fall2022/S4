import secrets, os
import atexit
import json
import hashlib
from tracemalloc import start
import requests
from io import BytesIO

from flask import Flask, request, flash, send_file, jsonify
from flask_restx import Api, Resource, fields

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(
    app,
    version="0.0.2",
    title="S4 Worker Node",
    description="Super Simple Storage System",
)

ns = api.namespace("", description="S4 API Endpoints")

# Fields
node_number = -1
url_array = []
main_url = ""

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

FILE_PATH = "./storage"
# FILE_PATH = os.getenv("FILE_PATH")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Endpoint parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
key_param = ns.parser()
key_param.add_argument("key", type=str)

filename_param = ns.parser()
filename_param.add_argument("filename", type=str)

main_url_param = ns.parser()
main_url_param.add_argument("mainUrl", type=str)

workers_param = ns.parser()
workers_param.add_argument("workers", type=list)

worker_idx_param = ns.parser()
worker_idx_param.add_argument("workerIndex", type=int)

forwarding_to_node_param = ns.parser()
forwarding_to_node_param.add_argument("forwardingToNode", type=str)

file_param = ns.parser()
file_param.add_argument("file", location="files", type=FileStorage)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Actual endpoints ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ----------------------------------- HealthCheck -----------------------------------
@ns.route("/HealthCheck")
class status_update(Resource):
    @ns.doc("HealthCheck")
    def get(self):
        return {"msg": f"Node {node_number} is alive."}, 200


# ----------------------------------- GetObject -----------------------------------
@ns.route("/GetObject")
@ns.expect(key_param)
class get_object(Resource):
    @ns.doc("GetObject")
    @api.response(200, "Success", model=GetObject200)
    @api.response(400, "Error: Bad Request", model=GetObject400)
    @api.response(404, "Error: Not Found", model=GetObject404)
    def get(self):

        # get the key from the request parameters
        args = request.args
        key = args.get("key")

        if not key:
            return {"msg": "Key not specified"}, 400

        # check if key exists
        r = requests.get(url=main_url + "FindObject", params={"key": key})

        if r.status_code == 404:
            return {"msg": "Key does not exist"}, 404
        elif r.status_code == 400:
            return r

        print("trying to get json")
        response = r.json()
        filename = response["filename"]
        print("got json")

        curr_replica = hash(key)
        start_replica = curr_replica
        if curr_replica == node_number:
            # this node is the primary replica
            res = retrieve_object(key, filename)
            if res:
                print("returning res")
                return res

        # try the first node
        try:
            r = requests.get(
                url_array[curr_replica] + "_GetObject",
                params={"key": key, "filename": filename},
                stream=True,
            )
            if r.status_code == 200:
                return send_file(
                    BytesIO(r.content), download_name=filename, as_attachment=True
                )
        except:
            pass
        curr_replica = (curr_replica + 1) % len(url_array)

        while curr_replica != start_replica:
            try:
                r = requests.get(
                    url_array[curr_replica] + "_GetObject",
                    params={"key": key, "filename": filename},
                )
                if r.status_code == 200:
                    return r.content, 200
            except:
                pass
            curr_replica = (curr_replica + 1) % len(url_array)

        return {"msg": "Invalid file specified"}, 404


# ----------------------------------- PutObject -----------------------------------
@ns.route("/PutObject")
@ns.expect(file_param, key_param, filename_param)
class put_object(Resource):
    @ns.doc("PutObject")
    @api.response(201, "Object successfully saved", model=PutObject201)
    @api.response(400, "Error: Bad Request", model=PutObject400)
    @api.response(404, "Error: Not Found", model=PutObject404)
    def put(self):

        # get the key from the request parameters
        args = request.args
        key = args.get("key")

        if not key:
            return {"msg": "Key not specified"}, 400

        # check response body for file
        if "file" not in request.files:
            return {"msg": "No file specified"}, 404

        file = request.files.get("file")
        filename = request.args.get("filename")
        # file checks
        if not filename:
            filename = secure_filename(file.filename)
        else:
            filename = secure_filename(filename)
        if not filename:
            return {"msg": "Empty filename"}, 400

        # check if key is unique
        r = requests.get(url=main_url + "/FindObject", params={"key": key})

        if r.status_code == 200:
            return {"msg": "Key not unique"}, 400
        elif r.status_code == 404:
            response = r.json()
            if not response["found"] == False:
                return {"msg": "Internal Server Error"}, 500

        curr_replica = hash(key)

        replicas = 2
        start_replica = curr_replica
        replica_nodes = []
        if curr_replica == node_number:
            # this node is the primary replica
            success = save_object(file, key)
            if success:
                replicas -= 1
                replica_nodes.append(url_array[curr_replica])
                curr_replica = (curr_replica + 1) % len(url_array)
                if curr_replica == start_replica:
                    replicas = 0

        file.seek(0)
        f = file.read()
        while replicas != 0:
            try:
                r = requests.put(
                    url_array[curr_replica] + "_PutObject",
                    params={"key": key},
                    files={"file": f},
                )
            except:
                print("Error while putting file")
                pass

            if r.status_code == 201:
                replicas -= 1
                replica_nodes.append(url_array[curr_replica])

            curr_replica = (curr_replica + 1) % len(url_array)

            if curr_replica == start_replica:
                # already performed linear traversal once
                break

        # TODO: do we need key and filename? why data vs. params?
        # Record data in main node
        r = requests.post(
            main_url + "RecordPutObject",
            data={"key": key, "filename": filename, "nodes": json.dumps(replica_nodes)},
        )

        return {"msg": "File successfully saved"}, 201


# ----------------------------------- ListObjects -----------------------------------
@ns.route("/ListObjects")
class list_objects(Resource):
    @ns.doc("ListObjects")
    @api.response(200, "Success", model=ListObjects200)
    def get(self):
        # Get key to file name mapping from main node
        r = requests.get(url=main_url + "ListObjects")
        if r.status_code == 200:
            response = r.json()
            keys_to_filenames = json.loads(response["objects"])
            return {
                "msg": "Files retrieved successfully.",
                "keysToFilenames": keys_to_filenames,
            }, 200
        elif r.status_code == 500:
            return {"msg": "The main node could not return the object mapping."}, 404
        else:
            return {"msg": "There was an error retrieving object names."}, r.status_code


# ----------------------------------- DeleteObject -----------------------------------
@ns.route("/DeleteObject")
@ns.expect(key_param)
class delete_object(Resource):
    @ns.doc("DeleteObject")
    @api.response(200, "Success", model=DeleteObject200)
    @api.response(400, "Error: Bad Request", model=DeleteObject400)
    @api.response(404, "Error: Not Found", model=DeleteObject404)
    def put(self):
        # get the key from the request parameters
        args = request.args
        key = args.get("key")
        if not key:
            return {"msg": "Key not specified"}, 400

        r = requests.post(main_url + "DeleteObject", params={"key": key})

        if r.status_code == 200:
            return {"msg": "The object was deleted successfully."}, 200
        else:
            # TODO: better way to do this?
            return {"msg": r.json()}, r.status_code


# ----------------------------------- Internal Endpoints -----------------------------------


@ns.route("/_GetObject")
@ns.expect(key_param)
@ns.expect(filename_param)
class _get_object(Resource):
    @ns.doc("_GetObject")
    @api.response(200, "Success", model=GetObject200)
    @api.response(400, "Error: Bad Request", model=GetObject400)
    @api.response(404, "Error: Not Found", model=GetObject404)
    def get(self):

        # get the key from the request parameters
        args = request.args
        key = args.get("key")
        filename = args.get("filename")

        res = retrieve_object(key, filename)

        if res:
            return res
        else:
            return {"msg": "Invalid file specified"}, 404


@ns.route("/_PutObject")
@ns.expect(key_param)
class _put_object(Resource):
    @ns.doc("_PutObject")
    @api.response(201, "Object successfully saved", model=PutObject201)
    @api.response(400, "Error: Bad Request", model=PutObject400)
    @api.response(404, "Error: Not Found", model=PutObject404)
    def put(self):
        args = request.args
        key = args.get("key")

        file = request.files.get("file")
        success = save_object(file, key)
        if not success:
            return {"msg": "Internal Server Error"}, 500

        return {"msg": "Object successfully saved"}, 201


@ns.route("/_DeleteObject")
@ns.expect(key_param)
class _delete_object(Resource):
    @ns.doc("_DeleteObject")
    # TODO add api response model
    def put(self):
        args = request.args
        key = args.get("key")

        try:
            # remove file from filesystem
            print(os.path.join(FILE_PATH, key))
            os.remove(os.path.join(FILE_PATH, key))
            return {"msg": "Object successfully deleted."}, 200
        except FileNotFoundError:
            return {"msg": f"Object with key {key} not found."}, 404
        except Exception as e:
            return {
                "msg": f"A {type(e).__name__} occurred while trying to delete the object."
            }, 400


@ns.route("/_ForwardObject")
@ns.expect(key_param)
@ns.expect(forwarding_to_node_param)
class _forward_object(Resource):
    def put(self):
        args = request.args
        key = args.get("key")
        forwardingToNode = args.get("forwardingToNode")
        file = open(os.path.join(FILE_PATH, key), "rb").read()

        print("\nforwardingTo: " + forwardingToNode + "\n")

        # url_array[forwardingToNode] + "/_PutObject",
        try:
            r = requests.put(
                url=forwardingToNode + "_PutObject",
                params={"key": key},
                files={"file": file},
            )
            return r.status_code

        except:
            pass


@ns.route("/_JoinNetwork")
class _join_network(Resource):
    @ns.doc("_JoinNetwork")
    # TODO add api response model
    def get(self):  # TODO is this get
        return 200


@ns.route("/_SetWorkers")
@ns.expect(workers_param)
@ns.expect(worker_idx_param)
@ns.expect(main_url_param)
class _set_workers(Resource):
    @ns.doc("_SetWorkers")
    # TODO add api response model
    def put(self):
        args = request.args
        global url_array
        global node_number
        global main_url
        url_array = json.loads(args.get("workers"))
        node_number = int(args.get("workerIndex"))
        main_url = args.get("mainUrl")
        return 200


# -----------------------------------Helper Functions -----------------------------------


def retrieve_object(key, filename):
    # try to get the file
    try:
        return send_file(os.path.join(FILE_PATH, key), download_name=filename)
    except:
        return False


def save_object(file, key):  # TODO decide if this should be filename or key
    print("Saving file: ", key)
    try:
        file.save(os.path.join(FILE_PATH, key))
        return True
    except:
        return False


def hash(key):
    bits = hashlib.md5(key.encode())
    node_idx = int(bits.hexdigest(), base=16) % len(url_array)
    return node_idx


# Main
if __name__ == "__main__":
    app.run(debug=True)
