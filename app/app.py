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


def get_linker_entities(text, ner_model, ref_part_model):
    """
    Extracts named entities and reference parts from the given text using the provided models.

    :param text: The input text to analyze.
    :param ner_model: The model for named entity recognition.
    :param ref_part_model: The model for reference part recognition.
    :return: A tuple containing lists of named entities and reference parts.
    """
    spans = ner_model.predict(text)
    cit_spans, other_spans = [], []
    for span in spans:
        if span.label == 'מקור':
            cit_spans.append(span)
        else:
            other_spans.append(span)
    ref_part_input = [span.text for span in cit_spans]
    ref_parts = ref_part_model.bulk_predict(ref_part_input, 150)
    return cit_spans, ref_parts, other_spans


def get_serialized_linker_entities(text, ner_model, ref_part_model, with_span_text=False):
    """
    Serializes named entities and reference parts from the given text using the provided models.

    :param text: The input text to analyze.
    :param ner_model: The model for named entity recognition.
    :param ref_part_model: The model for reference part recognition.
    :param with_span_text: Whether to include the span text in the serialized output.
    :return: A list of serialized named entities and ref parts.
    """
    cit_spans, ref_parts_list, other_spans = get_linker_entities(text, ner_model, ref_part_model)
    serial = [span.serialize(with_span_text) for span in other_spans]
    for span, ref_parts in zip(cit_spans, ref_parts_list):
        serialized_span = span.serialize(with_span_text)
        serialized_span['ref_parts'] = [part.serialize(with_span_text) for part in ref_parts]
        serial.append(serialized_span)
    return serial


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
        ref_part_model = models_by_type_and_lang['ref_part'][data['lang']]
        return jsonify(get_serialized_linker_entities(data['text'], ner_model, ref_part_model, with_span_text)), 200
    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
