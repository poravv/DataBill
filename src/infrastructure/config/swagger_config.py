from flasgger import Swagger
from flask_cors import CORS

def configure_swagger(app):
    CORS(app, resources={
        r"/docs/*": {"origins": "*"},
        r"/flasgger_static/*": {"origins": "*"},
        r"/apispec_1.json": {"origins": "*"}
    })
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Invoice Processing API",
            "description": "API Documentation for Invoice Processing System",
            "version": "1.0",
            "contact": {
                "name": "Lic. Andres Vera",
                "email": "your.email@example.com"
            }
        },
        "host": "localhost:5000",  # Agregado host
        "basePath": "/api/v1",     # Agregado basePath
        "schemes": ["http", "https"]
    }
    
    swagger_config = {
        "headers": [],
        "specs": [{
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs",
        "swagger_ui_bundle_js": "//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js",
        "swagger_ui_standalone_preset_js": "//unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js",
        "swagger_ui_css": "//unpkg.com/swagger-ui-dist@3/swagger-ui.css",
        "swagger_ui_config": {
            "deepLinking": True,
            "displayRequestDuration": True,
            "filter": True
        }
    }

    return Swagger(app, template=swagger_template, config=swagger_config)
