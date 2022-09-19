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

# API Model for example header/body and the response
key_example = api.model(
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
            example = "For now, it's the actual filename. We will eventually replace filename with the" + 
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
            example = "[image.jpeg, file.txt]",
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
            example = "[]",
        ),
    },
)

FILE_PATH = os.getenv("FILE_PATH")

# Endpoints

### Check if we can remove that later
@ns.route("/generateKey")
class generateKey(Resource):
    @ns.doc("generateKey")
    @api.response(200, "Success", model=key_example)
    def get(self):
        return {"Key": secrets.token_urlsafe(nbytes=16)}

@ns.route("/GetObject/?Key=<string:Key>")
class getFile(Resource):
    @ns.doc("GetObject")
    @api.response(200, "Success", model=GetObject_example)
    def get(self, Key):
        if not Key:
            return {"msg": "Key not specified"}, 400
        if not allowed_file(Key):
            return {"msg": "Invalid file specified"}, 404
        try:
            return send_file(os.path.join(FILE_PATH, Key))
        except:
            return {"msg": "Invalid file specified", }, 404

@ns.route("/ListObjects")
class listFiles(Resource):
    @ns.doc("ListObjects")
    @api.response(200, "Success", model=ListObjects_example)
    def get(self):
        dirs_files = os.listdir(FILE_PATH)
        onlyFiles = []
        for f in dirs_files:
            # get only files
            if os.path.isfile(os.path.join(FILE_PATH, f)) and allowed_file(f):
                onlyFiles.append(f)
        return {"msg": "Files retrieved successfully", "files": onlyFiles}, 200

upload_parser = ns.parser()
upload_parser.add_argument('file', 
                           location='files',
                           type=FileStorage)

@ns.route("/PutObject/?Key=<string:Key>")
@ns.expect(upload_parser)
class uploadFile(Resource):
    @ns.doc("PutObject")
    @api.response(201, "Object successfully saved", model=PutObject_example)
    @api.response(400, "Empty filepath")
    @api.response(404, "No file specified")
    def put(self, Key):
        if not Key:
            return {"msg": "Key not specified"}, 400
        
        if "file" not in request.files:
            return {"msg": "No file specified"}, 404

        args = upload_parser.parse_args()
        file = args.get("file")

        # unless we literally name a file empty, i dont know how to hit this conditional
        if file.filename == "":
            flash("Empty filepath")
            return {"msg": "Empty filename"}, 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(FILE_PATH, filename))

        return {"msg": "File successfully saved"}, 201

def allowed_file(filename):
    # PROBABLY NEEDS TO BE CHANGED CUZ WE ARE USING OBJECTS INSTEAD
    ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Main
if __name__ == "__main__":
    app.run(debug=True)