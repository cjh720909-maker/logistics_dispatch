from flask import Flask
from routes.dispatch import dispatch_bp
from routes.loading import loading_bp
from routes.menu_300_print import print_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(dispatch_bp)
    app.register_blueprint(loading_bp)
    app.register_blueprint(print_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)