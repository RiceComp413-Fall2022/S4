from flask import Flask
from flask_restx import Api, Resource, fields
from werkzeug.middleware.proxy_fix import ProxyFix
import secrets

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

# quick question: do we need a separate class for all of the endpoints?

# Endpoints
@ns.route("/generateKey")
class generateKey(Resource):
    """Route for generating a new API key"""

    @ns.doc("generateKey")
    @api.response(200, "Success", model=key)         # response.status_code returned?
    def get(self):
        return {"Key": secrets.token_urlsafe(nbytes=16)}

# @ns.route("/getObject", methods=['GET'])
# class getObject():
#     def get(self):
#         return "hello world"
    
# @ns.route("/putObject", methods=['PUT'])
# class getObject():
#     def put(self):
#         return "meow"
    
# Main
if __name__ == "__main__":
    app.run(debug=True)
