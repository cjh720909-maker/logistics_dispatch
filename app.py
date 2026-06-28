from flask import Flask

from dispatch.routes import dispatch_bp
from master.routes import master_bp
from print.routes import print_bp
from system.routes import system_bp

from utils.jinja_filters import (
    blank_zero,
    number_format,
    blank_none,
)


def create_app():
    app = Flask(__name__)

    app.register_blueprint(dispatch_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(print_bp)
    app.register_blueprint(system_bp)

    app.jinja_env.filters["blank_zero"] = blank_zero
    app.jinja_env.filters["number_format"] = number_format
    app.jinja_env.filters["blank_none"] = blank_none

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)