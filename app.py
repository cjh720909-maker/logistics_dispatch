from flask import Flask
from routes.dispatch_220 import dispatch_bp
from routes.menu_300_print import print_bp
from utils.jinja_filters import blank_zero
from utils.jinja_filters import number_format
from utils.jinja_filters import blank_none
from routes.menu_100_master import master_bp
from routes.loading_list_330 import loading_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(dispatch_bp)
    app.register_blueprint(loading_bp)
    app.register_blueprint(print_bp)
    app.register_blueprint(master_bp)
    app.jinja_env.filters["blank_zero"] = blank_zero

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)