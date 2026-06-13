from flask import Flask
from routes.dispatch import dispatch_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(dispatch_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)