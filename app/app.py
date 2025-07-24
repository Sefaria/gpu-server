from flask import Flask, request, jsonify
from named_entity_recognizer import NERFactory
from ne_span import NESpan


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
    app = Flask(__name__)
    app.config.from_object('config.BaseConfig')
    app.config.from_object('local_config.LocalConfig')

    with app.app_context():
        models_by_type_and_lang = create_models_from_config(app.config)

    @app.route('/recognize-entities', methods=['POST'])
    def recognize_entities():
        data = request.get_json(silent=True)
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' in request body."}), 400
        with_span_text = request.args.get('with_span_text', '0') == '1'
        ner_model = models_by_type_and_lang['named_entity'][data['lang']]
        spans: list[NESpan] = ner_model.predict(data['text'])
        return jsonify({"spans": [
            span.serialize(with_span_text) for span in spans
        ]}), 200
    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
