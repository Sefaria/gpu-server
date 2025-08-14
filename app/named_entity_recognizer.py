from abc import ABC, abstractmethod
from typing import Any
from tempfile import TemporaryDirectory
from ne_span import NESpan, NEDoc
from google_storage_manager import GoogleStorageManager
import spacy


class NERFactory:
    @staticmethod
    def create(model_type: str, model_location: str) -> 'AbstractNER':
        if model_type == "spacy":
            return SpacyNER(model_location)
        elif model_type == "huggingface":
            return HuggingFaceNER(model_location)
        else:
            raise ValueError(f"Unknown model type: {model_type}")


class AbstractNER(ABC):

    @abstractmethod
    def __init__(self, model_location: str):
        """
        Initializes the inference model with the specified model name.

        :param model_location: The name of the model to load.
        """
        pass

    @abstractmethod
    def predict(self, text: str) -> list[NESpan]:
        """
        Predicts the named entities in the given text.

        :param text: The input text to analyze.
        :return: A list of named entities found in the text.
        """
        pass

    @abstractmethod
    def bulk_predict(self, texts: list[str], batch_size: int) -> list[list[NESpan]]:
        """
        Predicts named entities for a list of texts.

        :param texts: A list of input texts to analyze.
        :param batch_size: Batch size for processing the texts.
        :return: A list of lists, where each inner list contains named entities for the corresponding text.
        """
        pass

    @abstractmethod
    def bulk_predict_as_tuples(self, text__context: list[tuple[str, Any]], batch_size: int) -> tuple[list[list[NESpan]], Any]:
        """
        Predicts named entities for a list of texts with additional context information.

        :param text__context: A list of input texts to analyze. Each text is paired with additional context information.
        :param batch_size: Batch size for processing the texts.
        :return: A tuple containing a list of lists of named entities and additional context information.
        """
        pass


class SpacyNER(AbstractNER):

    def __init__(self, model_location: str):
        self.__ner = self.__load_model(model_location)

    @staticmethod
    def __load_model(path: str):
        from spacy_function_registry import inner_punct_tokenizer_factory  # this looks unused, but spacy.load() expects this function to be in scope

        using_gpu = spacy.prefer_gpu()

        if path.startswith("gs://"):
            tar_buffer = GoogleStorageManager.get_tar_buffer(path)
            with TemporaryDirectory() as tempdir:
                tar_buffer.extractall(tempdir)
                nlp = spacy.load(tempdir)
        else:
            nlp = spacy.load(path)
        return nlp

    @staticmethod
    def __doc_to_ne_spans(doc) -> list[NESpan]:
        ne_doc = NEDoc(doc.text)
        return [NESpan(ne_doc, ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]

    def predict(self, text: str) -> list[NESpan]:
        return self.__doc_to_ne_spans(self.__ner(text))

    def bulk_predict(self, texts: list[str], batch_size: int) -> list[list[NESpan]]:
        return [self.__doc_to_ne_spans(doc) for doc in self.__ner.pipe(texts, batch_size=batch_size)]

    def bulk_predict_as_tuples(self, text__context: list[tuple[str, Any]], batch_size: int) -> tuple[list[list[NESpan]], Any]:
        ret = []
        for doc__context in self.__ner.pipe(text__context, batch_size=batch_size, as_tuples=True):
            doc, context = doc__context
            ret.append((self.__doc_to_ne_spans(doc), context))
        return ret


class HuggingFaceNER(AbstractNER):
    """

    - Loads a token-classification model + tokenizer (local path or HF Hub id).
    - Supports loading a tar.gz from GCS (same convention as SpacyNER).
    - Uses the pipeline() with aggregation_strategy="simple" to get character offsets.
    - Returns NESpan objects built from (start, end, label).
    """
    LABEL2ID = {
        "O": 0,
        "I-מקור": 1,
        "I-בן-אדם": 2,
        "B-מקור": 3,
        "B-בן-אדם": 4
    }

    def __init__(self, model_location: str):
        self.__tmpdir = None
        self.__pipe = self.__load_pipeline(model_location)

    def __load_pipeline(self, model_location: str):
        # Lazily import so the rest of the module can be used without transformers installed
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
        except ImportError as e:
            raise ImportError(
                "HuggingFaceNER requires the 'transformers' and 'torch' packages."
            ) from e
        local_location = model_location
        if model_location.startswith("gs://"):
            # Expecting a tar.gz of the *contents* of the model folder (not the folder itself)
            tar_buffer = GoogleStorageManager.get_tar_buffer(model_location)
            # Save temp dir because transformers can lazy load the model and tokenizer
            self.__tmpdir = TemporaryDirectory()
            tar_buffer.extractall(self.__tmpdir.name)
            local_location = self.__tmpdir.name

        # Load tokenizer/model and build a pipeline
        tokenizer = AutoTokenizer.from_pretrained(local_location)
        self.__model = AutoModelForTokenClassification.from_pretrained(
            local_location,
            label2id=self.LABEL2ID,
            id2label={i: label for label, i in self.LABEL2ID.items()}
        )
        device = 0 if torch.cuda.is_available() else -1

        return pipeline(
            task="ner",
            model=self.__model,
            tokenizer=tokenizer,
            aggregation_strategy="first",
            device=device,
            stride=128
        )

    @staticmethod
    def __ents_to_ne_spans(text: str, ents: list[dict]) -> list[NESpan]:
        ne_doc = NEDoc(text)
        return [
            NESpan(ne_doc, ent['start'], ent['end'], ent['entity_group']) for ent in ents
        ]

    def predict(self, text: str) -> list[NESpan]:
        ents = self.__pipe(text)
        # HF returns a list[dict] for a single string
        return self.__ents_to_ne_spans(text, ents)

    def bulk_predict(self, texts: list[str], batch_size: int) -> list[list[NESpan]]:
        # HF returns list[list[dict]] for list[str]
        all_ents = self.__pipe(texts, batch_size=batch_size)
        return [self.__ents_to_ne_spans(t, ents) for t, ents in zip(texts, all_ents)]

    def bulk_predict_as_tuples(
            self, text__context: list[tuple[str, Any]], batch_size: int
    ) -> tuple[list[list[NESpan]], Any]:
        texts = [t for t, _ in text__context]
        contexts = [c for _, c in text__context]
        all_ents = self.__pipe(texts, batch_size=batch_size)

        ret: list[tuple[list[NESpan], Any]] = []
        for t, ents, ctx in zip(texts, all_ents, contexts):
            ret.append((self.__ents_to_ne_spans(t, ents), ctx))
        return ret  # type: ignore[return-value]

    def __del__(self):
        # Ensure tempdir (if any) is cleaned up when the instance is garbage-collected
        try:
            if self.__tmpdir is not None:
                self.__tmpdir.cleanup()
        except Exception:
            pass
