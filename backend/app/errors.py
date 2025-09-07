from flask import Blueprint, jsonify, request
from werkzeug.http import HTTP_STATUS_CODES
from app import db
import traceback

bp = Blueprint('errors', __name__)

def error_response(status_code, message=None):
  payload={'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}

  if message:
    payload['message']=message
  payload['status_code']=status_code
  return jsonify(payload), status_code

@bp.app_errorhandler(400)
def bad_request(error):
  return error_response(400, 'Bad request - please check your input data')

@bp.app_errorhandler(404)
def not_found(error):
  return error_response(404, 'Resource not found')

@bp.app_errorhandler(405)
def method_not_allowed(error):
  return error_response(405, f'Method {request.method} not allowed for this endpoint')

@bp.app_errorhandlers(413)
def request_entity_too_large(error):
  return error_response(413, 'File too large - maximum size is 16MB')

@bp.app_errorhandler(429)
def ratelimit_handler(error):
  return error_response(429, 'Rate limit exceeded - please try again later')

@bp.app_errorhandler(500)
def internal_error(error):
  db.session.rollback()
  return error_response(500, 'An internal server error occured')

@bp.app_errorhandler(Exception)
def handler_unexpeced_error(error):
  db.session.rollback()

  import logging
  logging.error(f'Unexpected error: {str(error)}')
  logging.error(traceback.format_exc())

  return error_response(500, 'An unexpected error occured')