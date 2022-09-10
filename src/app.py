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

todo = api.model(
    "Todo",
    {
        "id": fields.Integer(readonly=True, description="The task unique identifier"),
        "task": fields.String(required=True, description="The task details"),
    },
)


@ns.route("/generateKey")
class generateKey(Resource):
    """Route for generating a new API key"""

    @ns.doc("generateKey")
    def get(self):
        return secrets.token_urlsafe(nbytes=16)


if __name__ == "__main__":
    app.run(debug=True)
