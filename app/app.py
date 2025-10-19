import json
import logging
import time
from functools import wraps
from flask import Flask, request, jsonify
from named_entity_recognizer import NERFactory
from app_helper import make_recognize_entities_output, make_bulk_recognize_entities_output


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': time.time(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        return json.dumps(log_entry)


def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    return logger


def timing_and_logging(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        endpoint = request.endpoint if hasattr(request, 'endpoint') else func.__name__
        method = request.method if hasattr(request, 'method') else 'UNKNOWN'
        
        logger.info(f"Starting {endpoint}", extra={'endpoint': endpoint, 'method': method})
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"Completed {endpoint}", extra={
                'endpoint': endpoint, 
                'method': method, 
                'duration': duration_ms
            })
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Error in {endpoint}: {str(e)}", extra={
                'endpoint': endpoint, 
                'method': method, 
                'duration': duration_ms
            })
            raise
    
    return wrapper


def create_models_from_config(config):
    model_configs = config['MODEL_PATHS']
    models_by_type_and_lang = {}
    for cfg in model_configs:
        model_type = cfg['type']
        if model_type not in models_by_type_and_lang:
            models_by_type_and_lang[model_type] = {}
        model = NERFactory.create(cfg['arch'], cfg['path'])
        models_by_type_and_lang[model_type][cfg['lang']] = model
    return models_by_type_and_lang


def create_app():
    logger = setup_logging()
    start_time = time.time()
    
    logger.info("Starting app creation")
    
    app = Flask(__name__)
    app.config.from_object('config.BaseConfig')
    app.config.from_envvar('APP_CONFIG')

    with app.app_context():
        models_by_type_and_lang = create_models_from_config(app.config)
    
    duration_ms = (time.time() - start_time) * 1000
    logger.info("App creation completed", extra={'duration': duration_ms})

    @app.route('/recognize-entities', methods=['POST'])
    @timing_and_logging
    def recognize_entities():
        data = request.get_json(silent=True)
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' in request body."}), 400
        with_span_text = request.args.get('with_span_text', '0') == '1'
        ner_model = models_by_type_and_lang['named_entity'][data['lang']]
        ref_part_model = models_by_type_and_lang['ref_part'][data['lang']]
        return jsonify(make_recognize_entities_output(data['text'], ner_model, ref_part_model, with_span_text)), 200

    @app.route('/bulk-recognize-entities', methods=['POST'])
    @timing_and_logging
    def bulk_recognize_entities():
        data = request.get_json(silent=True)
        if not data or 'texts' not in data:
            return jsonify({"error": "Missing 'texts' in request body."}), 400
        with_span_text = request.args.get('with_span_text', '0') == '1'
        ner_model = models_by_type_and_lang['named_entity'][data['lang']]
        ref_part_model = models_by_type_and_lang['ref_part'][data['lang']]
        texts = data['texts']
        results = make_bulk_recognize_entities_output(texts, ner_model, ref_part_model, with_span_text)
        return jsonify(results), 200
    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
