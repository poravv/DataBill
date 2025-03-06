from flask import Blueprint, request, jsonify
from flasgger import swag_from
from .api_specs import (
    INVOICE_UPLOAD_SPEC,
    INVOICE_LIST_SPEC,
    INVOICE_UPDATE_SPEC,
    EXPORT_JSON_SPEC
)
from ...application.ports.input.process_invoice_use_case import ProcessInvoiceUseCase

api = Blueprint('api', __name__, url_prefix='/api/v1')

@api.route('/invoice/upload', methods=['POST'])
@swag_from(INVOICE_UPLOAD_SPEC)
def upload_invoice():
    # Implementation
    pass

@api.route('/invoices', methods=['GET'])
@swag_from(INVOICE_LIST_SPEC)
def get_invoices():
    # Implementation
    pass

@api.route('/invoice/<invoice_id>', methods=['PUT'])
@swag_from(INVOICE_UPDATE_SPEC)
def update_invoice(invoice_id):
    # Implementation
    pass

@api.route('/export/json', methods=['GET'])
@swag_from(EXPORT_JSON_SPEC)
def export_json():
    # Implementation
    pass
