from functools import reduce
from collections import defaultdict
from ne_span import NESpan


BATCH_SIZE = 150
LABEL2TYPE = {
    'מקור': 'citation',
    'Citation': 'citation',
}


def make_recognize_entities_output(text, ner_model, ref_part_model, with_span_text=False):
    cit_spans, ref_parts_list, other_spans = _get_linker_entities(text, ner_model, ref_part_model)
    return _serialize_linker_entities(cit_spans, ref_parts_list, other_spans, with_span_text)


def make_bulk_recognize_entities_output(texts, ner_model, ref_part_model, with_span_text=False):
    results = _bulk_get_linker_entities(texts, ner_model, ref_part_model)
    return _bulk_serialize_linker_entities(results, with_span_text)


def _get_linker_entities(text, ner_model, ref_part_model):
    """
    Extracts named entities and reference parts from the given text using the provided models.

    :param text: The input text to analyze.
    :param ner_model: The model for named entity recognition.
    :param ref_part_model: The model for reference part recognition.
    :return: A tuple containing lists of named entities and reference parts.
    """
    spans = ner_model.predict(text)
    cit_spans, other_spans = _partition_spans(spans)
    ref_part_input = [span.text for span in cit_spans]
    ref_parts = ref_part_model.bulk_predict(ref_part_input, BATCH_SIZE)
    return cit_spans, ref_parts, other_spans


def _partition_spans(spans: list[NESpan]):
    cit_spans, other_spans = [], []
    for span in spans:
        if LABEL2TYPE.get(span.label) == 'citation':
            cit_spans.append(span)
        else:
            other_spans.append(span)
    return cit_spans, other_spans


def _bulk_partition_spans(spans_list: list[list[NESpan]]):
    cit_spans_list, other_spans_list = [], []
    for spans in spans_list:
        inner_cit_spans, inner_other_spans = _partition_spans(spans)
        cit_spans_list += [inner_cit_spans]
        other_spans_list += [inner_other_spans]
    return cit_spans_list, other_spans_list


def _bulk_get_linker_entities(texts, ner_model, ref_part_model):
    spans_list = ner_model.bulk_predict(texts, BATCH_SIZE)
    cit_spans_list, other_spans_list = _bulk_partition_spans(spans_list)

    ref_part_input = reduce(lambda a, b: a + [(sub_b.text, b[0]) for sub_b in b[1]], enumerate(cit_spans_list), [])
    all_raw_ref_part_spans = list(ref_part_model.bulk_predict_as_tuples(ref_part_input, BATCH_SIZE))
    all_raw_ref_part_span_map = defaultdict(list)
    for ref_part_span, input_idx in all_raw_ref_part_spans:
        all_raw_ref_part_span_map[input_idx] += [ref_part_span]

    output = []
    for input_idx, (cit_spans, other_spans) in enumerate(zip(cit_spans_list, other_spans_list)):
        ref_parts_list = all_raw_ref_part_span_map[input_idx]
        output += [(cit_spans, ref_parts_list, other_spans)]
    return output


def _serialize_linker_entities(cit_spans, ref_parts_list, other_spans, with_span_text=False):
    serial = [span.serialize(with_span_text) for span in other_spans]
    for span, ref_parts in zip(cit_spans, ref_parts_list):
        serialized_span = span.serialize(with_span_text)
        serialized_span['parts'] = [part.serialize(with_span_text) for part in ref_parts]
        serial.append(serialized_span)
    return {'entities': serial}


def _bulk_serialize_linker_entities(results, with_span_text=False):
    serial = []
    for cit_spans, ref_parts_list, other_spans in results:
        serial.append(_serialize_linker_entities(cit_spans, ref_parts_list, other_spans, with_span_text))
    return {'results': serial}
