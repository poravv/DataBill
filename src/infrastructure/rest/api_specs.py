INVOICE_UPLOAD_SPEC = {
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
}

INVOICE_LIST_SPEC = {
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
}

INVOICE_UPDATE_SPEC = {
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
}

EXPORT_JSON_SPEC = {
    'tags': ['Export'],
    'summary': 'Export all invoices as JSON',
    'responses': {
        200: {
            'description': 'JSON export of all invoices'
        }
    }
}
