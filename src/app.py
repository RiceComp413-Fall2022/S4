import secrets, os

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
    title="S4",
    description="Super Simple Storage System",
)

ns = api.namespace("S4", description="S4 API Endpoints")

# --------------------- API Model for example header/body and the response ---------------------
Key_example = api.model(
    "Key",
    {
        "Key": fields.String(
            required = True,
            description = "Newly generated API key",
            example = "j4ZRylUaPzz1wv2pahMYBA",
        ),
    }, 
)

GetObject_example = api.model(
    "GetObject", 
    {
        "GetObject": fields.String(
            required = True,
            description = "Get an object by the object name (perhaps object ID or object HASH)",
            example = "For now, it's the actual filename, like bob.txt. We will eventually replace filename with the" + 
                    "object's actual ID/HASH.",
        ),
    },
)

ListObjects_example = api.model(
    "ListObjects", 
    {
        "ListObjects": fields.String(
            required = True,
            description = "List of object names in storage.",
            example = "[image.jpeg, file.txt, test.pdf]",
        ),
    },
)

PutObject_example = api.model(
    "PutObject", 
    {
        "Key": fields.String(
            required = True,
            description = "Puts an object into the specified filepath (for now). Currently, the object is " + 
                          "placed somewhere on your local filesystem.",
            example = "Can return something like the filepath it was stored in, so /Users/bob/test.txt",
        ),
    },
)

FILE_PATH = os.getenv("FILE_PATH")

# --------------------------------------- Endpoint parameters ---------------------------------------
key_param = ns.parser()
key_param.add_argument('Key', type=str)

file_param = ns.parser()
file_param.add_argument('file', 
                           location='files',
                           type=FileStorage)

# --------------------------------------- Actual endpoints ---------------------------------------

# --------------------------- GenerateKey ---------------------------
### Check if we can remove that later
@ns.route("/generateKey")
class generateKey(Resource):
    @ns.doc("generateKey")
    @api.response(200, "Success", model=Key_example)
    def get(self):
        return {"Key": secrets.token_urlsafe(nbytes=16)}

# --------------------------- GetObject ---------------------------
@ns.route("/GetObject")
@ns.expect(key_param)
class getObject(Resource):
    @ns.doc("GetObject")
    @api.response(200, "Success", model=GetObject_example)
    def get(self):
        # get the key from the request parameters
        args = request.args
        Key = args.get("Key")
        
        # need a key
        if not Key:
            return {"msg": "Key not specified"}, 400
        
        # try to get the file
        try:
            return send_file(os.path.join(FILE_PATH, Key))
        except:
            return {"msg": "Invalid file specified"}, 404

# --------------------------- PutObject ---------------------------
@ns.route("/PutObject")
@ns.expect(file_param, key_param)
class putObject(Resource):
    @ns.doc("PutObject")
    @api.response(201, "Object successfully saved", model=PutObject_example)
    @api.response(400, "Empty filepath")
    @api.response(404, "No file specified")
    def put(self):
        # get the key from the request parameters
        args = request.args
        Key = args.get("Key")
        
        # need a key
        if not Key:
            return {"msg": "Key not specified"}, 400
        
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
                file.save(os.path.join(FILE_PATH, filename))

        return {"msg": "File successfully saved"}, 201
    
# --------------------------- ListObjects ---------------------------
@ns.route("/ListObjects")
class listObjects(Resource):
    @ns.doc("ListObjects")
    @api.response(200, "Success", model=ListObjects_example)
    def get(self):
        dirs_files = os.listdir(FILE_PATH)
        onlyFiles = []
        
        # list the files
        for f in dirs_files:
            # get only files
            if os.path.isfile(os.path.join(FILE_PATH, f)):
                onlyFiles.append(f)
        return {"msg": "Files retrieved successfully", "files": onlyFiles}, 200

# Main
if __name__ == "__main__":
    app.run(debug=True)
