class BaseConfig:
    GOOGLE_APPLICATION_CREDENTIALS_FILEPATH = None
    # Define at most 4 models, one for each language and type
    # 'arch' is the architecture of the model, e.g., 'spacy' or 'huggingface'
    # 'lang' is the language of the model, e.g., 'he' for Hebrew or 'en' for English
    # type is 'ref_part' or 'named_entity'
    MODEL_PATHS = [
        {
            'arch': 'spacy',
            'lang': 'he',
            'path': None,
            'type': 'ref_part'
        }
    ]
