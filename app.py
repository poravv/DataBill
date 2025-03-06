import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import openai
import base64
import json
from pymongo import MongoClient
from bson import ObjectId
import pandas as pd
from datetime import datetime
from flasgger import Swagger, swag_from
from src.infrastructure.config.swagger_config import configure_swagger
from src.infrastructure.rest.api_controllers import api
from flask_cors import CORS

# Cargar variables de entorno
load_dotenv()

# Configuración Flask
def create_app():
    app = Flask(__name__, static_folder='static')
    CORS(app)  # Habilitar CORS globalmente
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Simplificar la configuración de Swagger, removiendo openapi
    app.config['SWAGGER'] = {
        'title': 'Invoice Processing API',
        'doc_dir': './docs/'
    }

    # Configuración Swagger
    swagger = configure_swagger(app)
    
    # Register API Blueprint
    app.register_blueprint(api)

    # Inicializar cliente OpenAI
    openai.api_key = os.getenv('OPENAI_API_KEY')

    # Inicializar cliente MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client[os.getenv('MONGODB_DB')]
    collection = db[os.getenv('MONGODB_COLLECTION')]

    # Formulario de subida
    class UploadForm(FlaskForm):
        image = FileField('Upload Invoice Image', validators=[DataRequired()])
        submit = SubmitField('Submit')

    # Formulario de edición de factura
    class EditInvoiceForm(FlaskForm):
        empresa_nombre = StringField('Empresa Nombre')
        empresa_razon_social = StringField('Empresa Razon Social')
        empresa_ruc = StringField('Empresa RUC')
        empresa_actividad = StringField('Empresa Actividad')
        empresa_direccion = StringField('Empresa Dirección')
        empresa_telefono = StringField('Empresa Teléfono')
        timbrado_numero = StringField('Timbrado Número')
        fecha_inicio_vigencia = StringField('Fecha Inicio Vigencia')
        valido_hasta = StringField('Válido Hasta')
        factura_numero = StringField('Factura Número')
        factura_fecha = StringField('Factura Fecha')
        caja = StringField('Caja')
        iva_incluido = StringField('IVA Incluido')
        cantidad_articulos = StringField('Cantidad Artículos')
        subtotal = StringField('Subtotal')
        total_a_pagar = StringField('Total a Pagar')
        cliente_nombre = StringField('Cliente Nombre')
        cliente_ruc = StringField('Cliente RUC')
        impuestos_exentas = StringField('Impuestos Exentas')
        impuestos_gravadas_5 = StringField('Impuestos Gravadas 5%')
        impuestos_gravadas_10 = StringField('Impuestos Gravadas 10%')
        estado = StringField('Estado')
        submit = SubmitField('Guardar')

    # Clase para manejar los datos de la factura
    class Invoice:
        def __init__(self, data):
            self.data = data

        def save_to_mongo(self):
            result = collection.insert_one(self.data)
            return str(result.inserted_id)

        @staticmethod
        def update_invoice(invoice_id, data):
            collection.update_one({'_id': ObjectId(invoice_id)}, {'$set': data})

    @app.route('/')
    def home():
        return render_template('home.html')

    # Modificar la ruta /upload para que sea separada
    @app.route('/upload', methods=['GET', 'POST'])
    def index():
        form = UploadForm()
        if form.validate_on_submit():
            image = form.image.data
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            return redirect(url_for('process_image', filename=filename))
        return render_template('index.html', form=form)

    # Procesar la imagen con OpenAI Vision
    @app.route('/process/<filename>')
    def process_image(filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404

        try:
            # Abrir la imagen en modo binario y codificarla en base64
            with open(filepath, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Modificar el prompt para obtener la estructura deseada
            prompt_text = """Extrae los datos de esta factura y devuélvelos en un JSON con exactamente esta estructura:
            {
                "empresa": {
                    "nombre": "",
                    "ruc": "",
                    "direccion": "",
                    "telefono": ""
                },
                "timbrado": {
                    "nro": "",
                    "fecha_inicio_vigencia": "",
                    "valido_hasta": ""
                },
                "factura": {
                    "contado_nro": "",
                    "fecha": "",
                    "caja_nro": ""
                },
                "productos": [
                    {
                        "articulo": "",
                        "cantidad": 0,
                        "precio_unitario": 0,
                        "total": 0
                    }
                ],
                "totales": {
                    "cantidad_articulos": 0,
                    "subtotal": 0,
                    "total_a_pagar": 0,
                    "iva_0%": 0,
                    "iva_5%": 0,
                    "iva_10%": 0,
                    "total_iva": 0
                },
                "cliente": {
                    "nombre": "",
                    "ruc": ""
                }
            }"""

            # Hacer la petición a GPT-4 Vision para analizar la imagen
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",  # Usar el modelo correcto
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                                }
                            ],
                        }
                    ],
                    max_tokens=1000
                )

                result = response.choices[0].message.content
                try:
                    if result.startswith("```json"):
                        result = result[7:-3].strip()
                    result_json = json.loads(result)
                    
                    # Asegurar la estructura correcta
                    required_structure = {
                        'empresa': {'nombre': '', 'ruc': '', 'direccion': '', 'telefono': ''},
                        'timbrado': {'nro': '', 'fecha_inicio_vigencia': '', 'valido_hasta': ''},
                        'factura': {'contado_nro': '', 'fecha': '', 'caja_nro': ''},
                        'productos': [],
                        'totales': {
                            'cantidad_articulos': 0,
                            'subtotal': 0,
                            'total_a_pagar': 0,
                            'iva_0%': 0,
                            'iva_5%': 0,
                            'iva_10%': 0,
                            'total_iva': 0
                        },
                        'cliente': {'nombre': '', 'ruc': ''},
                        'estado': 'pendiente'
                    }

                    # Asegurar que existan todas las secciones necesarias
                    for key, default_value in required_structure.items():
                        if key not in result_json:
                            result_json[key] = default_value

                    # Crear instancia de Invoice y guardar en MongoDB
                    invoice = Invoice(result_json)
                    invoice_id = invoice.save_to_mongo()
                    result_json['_id'] = invoice_id

                    return render_template('result.html', result=result_json)

                except json.JSONDecodeError:
                    return jsonify({"error": "Invalid JSON response from OpenAI"}), 500

            except Exception as e:
                return jsonify({
                    "error": str(e),
                    "message": "Error processing the image. Please try again."
                }), 500

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Ruta para mostrar la grilla de facturas
    @app.route('/invoices')
    def invoices():
        page = int(request.args.get('page', 1))
        per_page = 10
        empresa_ruc = request.args.get('empresa_ruc', '')
        cliente_ruc = request.args.get('cliente_ruc', '')
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        
        # Construir query
        query = {'estado': {'$ne': 'anulado'}}
        if empresa_ruc:
            query['empresa.ruc'] = {'$regex': empresa_ruc, '$options': 'i'}
        if cliente_ruc:
            query['cliente.ruc'] = {'$regex': cliente_ruc, '$options': 'i'}
        if fecha_desde or fecha_hasta:
            query['factura.fecha'] = {}
            if fecha_desde:
                query['factura.fecha']['$gte'] = fecha_desde
            if fecha_hasta:
                query['factura.fecha']['$lte'] = fecha_hasta

        # Contar total de documentos para paginación
        total_docs = collection.count_documents(query)
        total_pages = (total_docs + per_page - 1) // per_page

        # Obtener documentos paginados
        invoices = list(collection.find(query)
                    .skip((page - 1) * per_page)
                    .limit(per_page))

        formatted_invoices = []
        for invoice in invoices:
            formatted_invoice = {
                '_id': str(invoice['_id']),
                'empresa': {
                    'nombre': invoice.get('empresa', {}).get('nombre', ''),
                    'ruc': invoice.get('empresa', {}).get('ruc', ''),
                    'direccion': invoice.get('empresa', {}).get('direccion', ''),
                    'telefono': invoice.get('empresa', {}).get('telefono', '')
                },
                'timbrado': {
                    'nro': invoice.get('timbrado', {}).get('nro', ''),
                    'fecha_inicio_vigencia': invoice.get('timbrado', {}).get('fecha_inicio_vigencia', ''),
                    'valido_hasta': invoice.get('timbrado', {}).get('valido_hasta', '')
                },
                'factura': {
                    'contado_nro': invoice.get('factura', {}).get('contado_nro', ''),
                    'fecha': invoice.get('factura', {}).get('fecha', ''),
                    'caja_nro': invoice.get('factura', {}).get('caja_nro', ''),
                    'iva_incluido': invoice.get('factura', {}).get('iva_incluido', '')
                },
                'productos': invoice.get('productos', []),
                'totales': {
                    'cantidad_articulos': invoice.get('totales', {}).get('cantidad_articulos', ''),
                    'subtotal': invoice.get('totales', {}).get('subtotal', ''),
                    'total_a_pagar': invoice.get('totales', {}).get('total_a_pagar', ''),
                    'importe_entregado': invoice.get('totales', {}).get('importe_entregado', ''),
                    'vuelto': invoice.get('totales', {}).get('vuelto', ''),
                    'iva_0': invoice.get('totales', {}).get('iva_0%', 0),
                    'iva_5': invoice.get('totales', {}).get('iva_5%', 0),
                    'iva_10': invoice.get('totales', {}).get('iva_10%', 0),
                    'total_iva': invoice.get('totales', {}).get('total_iva', 0)
                },
                'cliente': {
                    'nombre': invoice.get('cliente', {}).get('nombre', ''),
                    'ruc': invoice.get('cliente', {}).get('ruc', '')
                },
                'detalle_iva': invoice.get('detalle_iva', {}),
                'estado': invoice.get('estado', 'pendiente')
            }
            formatted_invoices.append(formatted_invoice)
        return render_template('invoices.html', 
                            invoices=formatted_invoices,
                            page=page,
                            total_pages=total_pages,
                            empresa_ruc=empresa_ruc,
                            cliente_ruc=cliente_ruc,
                            fecha_desde=fecha_desde,
                            fecha_hasta=fecha_hasta)

    # Ruta para exportar las facturas a XLSX
    @app.route('/export')
    def export():
        invoices = list(collection.find())
        data = []
        for invoice in invoices:
            # Create a flattened structure for Excel
            productos = invoice.get('productos', [])
            productos_str = "\n".join([
                f"{p.get('articulo', '')} ({p.get('cantidad', '')}x{p.get('precio_unitario', '')}={p.get('total', '')})"
                for p in productos
            ])
            
            # Acceder correctamente a los datos anidados
            empresa = invoice.get('empresa', {})
            row = {
                "ID": str(invoice.get('_id', '')),
                # Empresa - corregido el acceso a los datos
                "Empresa Nombre": empresa.get('nombre', ''),
                "Empresa RUC": empresa.get('ruc', ''),
                "Empresa Dirección": empresa.get('direccion', ''),
                "Empresa Teléfono": empresa.get('telefono', ''),
                # Resto de los campos
                "Timbrado Número": invoice.get('timbrado', {}).get('nro', ''),
                "Fecha Inicio Vigencia": invoice.get('timbrado', {}).get('fecha_inicio_vigencia', ''),
                "Válido Hasta": invoice.get('timbrado', {}).get('valido_hasta', ''),
                "Número Factura": invoice.get('factura', {}).get('contado_nro', ''),
                "Fecha Factura": invoice.get('factura', {}).get('fecha', ''),
                "Caja Número": invoice.get('factura', {}).get('caja_nro', ''),
                "Productos": productos_str,
                "Cantidad Items": len(productos),
                "Subtotal": invoice.get('totales', {}).get('subtotal', ''),
                "Total a Pagar": invoice.get('totales', {}).get('total_a_pagar', ''),
                "Cliente Nombre": invoice.get('cliente', {}).get('nombre', ''),
                "Cliente RUC": invoice.get('cliente', {}).get('ruc', ''),
                "IVA 0%": invoice.get('totales', {}).get('iva_0%', 0),
                "IVA 5%": invoice.get('totales', {}).get('iva_5%', 0),
                "IVA 10%": invoice.get('totales', {}).get('iva_10%', 0),
                "Total IVA": invoice.get('totales', {}).get('total_iva', 0),
                "Estado": invoice.get('estado', 'pendiente')
            }
            data.append(row)

        df = pd.DataFrame(data)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'invoices.xlsx')
        df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True)

    # Modificar la ruta de verify_invoices
    @app.route('/verify_invoices', methods=['GET', 'POST'])
    def verify_invoices():
        if request.method == 'POST':
            invoice_id = request.form.get('invoice_id')
            
            # Primero obtener el documento existente
            existing_invoice = collection.find_one({'_id': ObjectId(invoice_id)})
            if not existing_invoice:
                return redirect(url_for('verify_invoices'))
            
            # Preparar datos de actualización manteniendo datos existentes
            update_data = {
                'empresa': {
                    'nombre': request.form.get('empresa_nombre', existing_invoice.get('empresa', {}).get('nombre', '')),
                    'ruc': request.form.get('empresa_ruc', existing_invoice.get('empresa', {}).get('ruc', '')),
                    'direccion': request.form.get('empresa_direccion', existing_invoice.get('empresa', {}).get('direccion', '')),
                    'telefono': request.form.get('empresa_telefono', existing_invoice.get('empresa', {}).get('telefono', ''))
                },
                'timbrado': {
                    'nro': request.form.get('timbrado_nro', existing_invoice.get('timbrado', {}).get('nro', '')),
                    'fecha_inicio_vigencia': request.form.get('timbrado_inicio', existing_invoice.get('timbrado', {}).get('fecha_inicio_vigencia', '')),
                    'valido_hasta': request.form.get('timbrado_fin', existing_invoice.get('timbrado', {}).get('valido_hasta', ''))
                },
                'factura': {
                    'contado_nro': request.form.get('factura_nro', existing_invoice.get('factura', {}).get('contado_nro', '')),
                    'fecha': request.form.get('factura_fecha', existing_invoice.get('factura', {}).get('fecha', '')),
                    'caja_nro': existing_invoice.get('factura', {}).get('caja_nro', ''),
                    'iva_incluido': existing_invoice.get('factura', {}).get('iva_incluido', '')
                },
                'productos': existing_invoice.get('productos', []),
                'totales': {
                    'cantidad_articulos': existing_invoice.get('totales', {}).get('cantidad_articulos', ''),
                    'subtotal': existing_invoice.get('totales', {}).get('subtotal', ''),
                    'total_a_pagar': existing_invoice.get('totales', {}).get('total_a_pagar', ''),
                    'total_iva': existing_invoice.get('totales', {}).get('total_iva', ''),
                    'iva_0%': existing_invoice.get('totales', {}).get('iva_0%', 0),
                    'iva_5%': existing_invoice.get('totales', {}).get('iva_5%', 0),
                    'iva_10%': existing_invoice.get('totales', {}).get('iva_10%', 0)
                },
                'cliente': existing_invoice.get('cliente', {}),
                'estado': request.form.get('estado', existing_invoice.get('estado', 'pendiente'))
            }

            # Actualizar documento
            collection.update_one(
                {'_id': ObjectId(invoice_id)},
                {'$set': update_data}
            )
            
            return redirect(url_for('verify_invoices'))

        # Obtener solo facturas pendientes
        invoices = list(collection.find({
            "$or": [
                {"estado": "pendiente"},
                {"estado": {"$exists": False}}
            ]
        }))
        
        # Formatear los datos
        formatted_invoices = []
        for invoice in invoices:
            formatted_invoice = {
                '_id': str(invoice['_id']),
                'empresa': invoice.get('empresa', {}),
                'timbrado': invoice.get('timbrado', {}),
                'factura': invoice.get('factura', {}),
                'productos': invoice.get('productos', []),
                'totales': invoice.get('totales', {}),
                'cliente': invoice.get('cliente', {}),
                'detalle_iva': invoice.get('detalle_iva', {}),
                'estado': invoice.get('estado', 'pendiente')
            }
            formatted_invoices.append(formatted_invoice)
        
        return render_template('verify_invoices.html', invoices=formatted_invoices)

    @app.route('/invoice/cancel/<invoice_id>', methods=['POST'])
    def cancel_invoice(invoice_id):
        try:
            collection.update_one(
                {'_id': ObjectId(invoice_id)},
                {'$set': {'estado': 'anulado'}}
            )
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # API Endpoints
    @app.route('/api/v1/invoice/upload', methods=['POST'])
    @swag_from({
        'tags': ['Invoices'],
        'summary': 'Upload and process invoice image',
        'parameters': [
            {
                'name': 'file',
                'in': 'formData',
                'type': 'file',
                'required': True,
                'description': 'Invoice image file'
            }
        ],
        'responses': {
            200: {
                'description': 'Invoice processed successfully',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'invoice_id': {'type': 'string'},
                        'data': {'type': 'object'}
                    }
                }
            }
        }
    })
    def api_upload_invoice():
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        try:
            # Procesar imagen usando el código existente
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Usar el código existente de process_image pero devolver JSON
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            if not os.path.exists(filepath):
                return jsonify({"error": "File not found"}), 404

            try:
                # Abrir la imagen en modo binario y codificarla en base64
                with open(filepath, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')

                # Modificar el prompt para obtener la estructura deseada
                prompt_text = """Extrae los datos de esta factura y devuélvelos en un JSON con exactamente esta estructura:
                {
                    "empresa": {
                        "nombre": "",
                        "ruc": "",
                        "direccion": "",
                        "telefono": ""
                    },
                    "timbrado": {
                        "nro": "",
                        "fecha_inicio_vigencia": "",
                        "valido_hasta": ""
                    },
                    "factura": {
                        "contado_nro": "",
                        "fecha": "",
                        "caja_nro": ""
                    },
                    "productos": [
                        {
                            "articulo": "",
                            "cantidad": 0,
                            "precio_unitario": 0,
                            "total": 0
                        }
                    ],
                    "totales": {
                        "cantidad_articulos": 0,
                        "subtotal": 0,
                        "total_a_pagar": 0,
                        "iva_0%": 0,
                        "iva_5%": 0,
                        "iva_10%": 0,
                        "total_iva": 0
                    },
                    "cliente": {
                        "nombre": "",
                        "ruc": ""
                    }
                }"""

                # Hacer la petición a GPT-4 Vision para analizar la imagen
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",  # Usar el modelo correcto
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt_text},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                                    }
                                ],
                            }
                        ],
                        max_tokens=1000
                    )

                    result = response.choices[0].message.content
                    try:
                        if result.startswith("```json"):
                            result = result[7:-3].strip()
                        result_json = json.loads(result)
                        
                        # Asegurar la estructura correcta
                        required_structure = {
                            'empresa': {'nombre': '', 'ruc': '', 'direccion': '', 'telefono': ''},
                            'timbrado': {'nro': '', 'fecha_inicio_vigencia': '', 'valido_hasta': ''},
                            'factura': {'contado_nro': '', 'fecha': '', 'caja_nro': ''},
                            'productos': [],
                            'totales': {
                                'cantidad_articulos': 0,
                                'subtotal': 0,
                                'total_a_pagar': 0,
                                'iva_0%': 0,
                                'iva_5%': 0,
                                'iva_10%': 0,
                                'total_iva': 0
                            },
                            'cliente': {'nombre': '', 'ruc': ''},
                            'estado': 'pendiente'
                        }

                        # Asegurar que existan todas las secciones necesarias
                        for key, default_value in required_structure.items():
                            if key not in result_json:
                                result_json[key] = default_value

                        # Crear instancia de Invoice y guardar en MongoDB
                        invoice = Invoice(result_json)
                        invoice_id = invoice.save_to_mongo()
                        result_json['_id'] = invoice_id

                        return jsonify({
                            'invoice_id': invoice_id,
                            'data': result_json
                        })

                    except json.JSONDecodeError:
                        return jsonify({"error": "Invalid JSON response from OpenAI"}), 500

                except Exception as e:
                    return jsonify({
                        "error": str(e),
                        "message": "Error processing the image. Please try again."
                    }), 500

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/v1/invoices', methods=['GET'])
    @swag_from({
        'tags': ['Invoices'],
        'summary': 'Get all invoices with pagination and filters',
        'parameters': [
            {
                'name': 'page',
                'in': 'query',
                'type': 'integer',
                'default': 1
            },
            {
                'name': 'per_page',
                'in': 'query',
                'type': 'integer',
                'default': 10
            },
            {
                'name': 'empresa_ruc',
                'in': 'query',
                'type': 'string'
            },
            {
                'name': 'cliente_ruc',
                'in': 'query',
                'type': 'string'
            }
        ],
        'responses': {
            200: {
                'description': 'List of invoices',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'total': {'type': 'integer'},
                        'pages': {'type': 'integer'},
                        'current_page': {'type': 'integer'},
                        'invoices': {'type': 'array'}
                    }
                }
            }
        }
    })
    def api_get_invoices():
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        empresa_ruc = request.args.get('empresa_ruc')
        cliente_ruc = request.args.get('cliente_ruc')
        
        query = {'estado': {'$ne': 'anulado'}}
        if empresa_ruc:
            query['empresa.ruc'] = {'$regex': empresa_ruc, '$options': 'i'}
        if cliente_ruc:
            query['cliente.ruc'] = {'$regex': cliente_ruc, '$options': 'i'}

        total = collection.count_documents(query)
        invoices = list(collection.find(query)
                    .skip((page - 1) * per_page)
                    .limit(per_page))
        
        return jsonify({
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'current_page': page,
            'invoices': [{**inv, '_id': str(inv['_id'])} for inv in invoices]
        })

    @app.route('/api/v1/invoice/<invoice_id>', methods=['PUT'])
    @swag_from({
        'tags': ['Invoices'],
        'summary': 'Update invoice data',
        'parameters': [
            {
                'name': 'invoice_id',
                'in': 'path',
                'required': True,
                'type': 'string'
            },
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {
                    'type': 'object'
                }
            }
        ],
        'responses': {
            200: {
                'description': 'Invoice updated successfully'
            }
        }
    })
    def api_update_invoice(invoice_id):
        try:
            data = request.get_json()
            collection.update_one(
                {'_id': ObjectId(invoice_id)},
                {'$set': data}
            )
            return jsonify({'message': 'Invoice updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/v1/export/json', methods=['GET'])
    @swag_from({
        'tags': ['Export'],
        'summary': 'Export all invoices as JSON',
        'responses': {
            200: {
                'description': 'JSON export of all invoices'
            }
        }
    })
    def api_export_json():
        try:
            invoices = list(collection.find())
            for inv in invoices:
                inv['_id'] = str(inv['_id'])
            return jsonify(invoices)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app

app = create_app()

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
