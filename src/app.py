import secrets, os
import atexit
import json

from flask import Flask, request, flash, send_file
from flask_restx import Api, Resource, fields

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from security import api_required

authorizations = {"apikey": {"type": "apiKey", "in": "header", "name": "X-API-KEY"}}

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(
    app,
    version="0.0.1",
    title="S4",
    description="Super Simple Storage System",
    authorizations=authorizations,
    security="apikey",
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

FILE_PATH = "./tests"
# FILE_PATH = os.getenv("FILE_PATH")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Endpoint parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
key_param = ns.parser()
key_param.add_argument("Key", type=str)

file_param = ns.parser()
file_param.add_argument("file", location="files", type=FileStorage)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Actual endpoints ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ----------------------------------- GenerateKey -----------------------------------
# @ns.route("/GenerateKey")
# class generateKey(Resource):
#     @ns.doc("GenerateKey")
#     @api.response(200, "Success", model=Key200)
#     def get(self):
#         return {"Key": secrets.token_urlsafe(nbytes=16)}

# ----------------------------------- GetObject -----------------------------------
@ns.route("/GetObject")
@ns.expect(key_param)
class getObject(Resource):
    @ns.doc("GetObject")
    @api.response(200, "Success", model=GetObject200)
    @api.response(400, "Error: Bad Request", model=GetObject400)
    @api.response(404, "Error: Not Found", model=GetObject404)
    @api_required
    def get(self):
        # TODO: make into a DAO layer with transactions
        with open("./keys.json", "r") as f:
            keys_to_files = json.load(f)

        # get the key from the request parameters
        args = request.args
        Key = args.get("Key")

        # check key
        if not Key:
            return {"msg": "Key not specified"}, 400
        if Key not in keys_to_files:
            return {"msg": "No object associated with key"}, 400

        # try to get the file
        try:
            return send_file(
                os.path.join("../" + FILE_PATH, Key), download_name=keys_to_files[Key]
            )
        except:
            return {"msg": "Invalid file specified"}, 404


# ----------------------------------- PutObject -----------------------------------
@ns.route("/PutObject")
@ns.expect(file_param, key_param)
class putObject(Resource):
    @ns.doc("PutObject")
    @api.response(201, "Object successfully saved", model=PutObject201)
    @api.response(400, "Error: Bad Request", model=PutObject400)
    @api.response(404, "Error: Not Found", model=PutObject404)
    @api_required
    def put(self):
        with open("./keys.json", "r") as f:
            keys_to_files = json.load(f)

        # get the key from the request parameters
        args = request.args
        Key = args.get("Key")

        # key checks
        if not Key:
            return {"msg": "Key not specified"}, 400
        if Key in keys_to_files:
            return {"msg": "Key not unique"}, 400

        # need a response body with a file in it
        if "file" not in request.files:
            return {"msg": "No file specified"}, 404

        args = file_param.parse_args()
        file = args.get("file")

        # file checks
        if file:
            filename = secure_filename(file.filename)
            if not filename:
                flash("Empty filepath")
                return {"msg": "Empty filename"}, 400
            else:
                keys_to_files[Key] = filename
                file.save(os.path.join(FILE_PATH, Key))
                with open("./keys.json", "w") as f:
                    f.write(json.dumps(keys_to_files))

        return {"msg": "File successfully saved"}, 201


# ----------------------------------- ListObjects -----------------------------------
@ns.route("/ListObjects")
class listObjects(Resource):
    @ns.doc("ListObjects")
    @api.response(200, "Success", model=ListObjects200)
    @api_required
    def get(self):
        with open("./keys.json", "r") as f:
            keys_to_files = json.load(f)
        return {"msg": "Files retrieved successfully", "files": keys_to_files}, 200


# ----------------------------------- DeleteObject -----------------------------------
@ns.route("/DeleteObject")
@ns.expect(key_param)
class deleteObject(Resource):
    @ns.doc("DeleteObject")
    @api.response(200, "Success", model=DeleteObject200)
    @api.response(400, "Error: Bad Request", model=DeleteObject400)
    @api.response(404, "Error: Not Found", model=DeleteObject404)
    @api_required
    def put(self):
        with open("./keys.json", "r") as f:
            keys_to_files = json.load(f)

        # get the key from the request parameters
        args = request.args
        Key = args.get("Key")

        # key checks
        if not Key:
            return {"msg": "Key not specified"}, 400
        if Key not in keys_to_files:
            return {"msg": "Key does not exist"}, 404

        # remove entry from json
        keys_to_files.pop(Key)
        with open("./keys.json", "w") as f:
            f.write(json.dumps(keys_to_files))

        # remove file from filesystem
        os.remove(os.path.join(FILE_PATH, Key))

        return {"msg": "File deleted successfully"}, 200


# Main
if __name__ == "__main__":
    app.run(debug=True)
