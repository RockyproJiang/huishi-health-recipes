from routes.auth import auth_bp
from routes.meals import meals_bp
from routes.health import health_bp
from routes.checkin import checkin_bp
from routes.favorites import favorites_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(meals_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(checkin_bp)
    app.register_blueprint(favorites_bp)
