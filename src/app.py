import secrets, os

from flask import Flask, request, redirect, flash, url_for
from flask_restx import Api, Resource, fields

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

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
key = api.model(
    "Key",
    {
        "Key": fields.String(
            required=True,
            description="Newly generated API key",
            example="j4ZRylUaPzz1wv2pahMYBA",
        ),
    },
)

UPLOAD_FOLDER = '/Users/ericy/Desktop'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Endpoints
@ns.route("/generateKey")
class generateKey(Resource):
    @ns.doc("generateKey")
    @api.response(200, "Success", model=key)         # response.status_code returned?
    def get(self):
        return {"Key": secrets.token_urlsafe(nbytes=16)}

# @ns.route("/getObject", methods=['GET'])
# class getObject(Resource):
#     @ns.doc("getObject")
#     @api.response(200, "Success", model=key)         # response.status_code returned?
#     def get(self):
#         return {"Key1": secrets.token_urlsafe(nbytes=16)}

# @ns.route("/putFile", methods=['PUT'])
# class uploadFile(Resource):
#     def allowed_file(filename):
#         return '.' in filename and \
#             filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#     @ns.doc("putFile")
#     @api.response(200, "Success", model=key)
#     def upload_file():
#         if request.method == 'PUT':
#             if 'file' not in request.files:
#                 flash('No file part')
#                 return redirect(request.url)
#             file = request.files['file']
            
#             if file.filename == '':
#                 flash('No selected file')
#                 return redirect(request.url)
#             if file and allowed_file(file.filename):
#                 filename = secure_filename(file.filename)
#                 file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#                 return redirect(url_for('download_file', name=filename))
#         return '''
#         <!doctype html>
#         <title>Upload new File</title>
#         <h1>Upload new File</h1>
#         <form method=post enctype=multipart/form-data>
#         <input type=file name=file>
#         <input type=submit value=Upload>
#         </form>
#         '''

# Main
if __name__ == "__main__":
    app.run(debug=True)
