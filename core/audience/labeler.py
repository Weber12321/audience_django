from typing import Iterable, List, Set, Dict

from tqdm import tqdm

from core.audience_models import AudienceModel
from core.dao.author_example import Author
from core.dao.input_example import InputExample
from core.helpers.log_helper import get_logger


def _run_labeling(audience_model: AudienceModel, doc: InputExample, author=None, bypass_labels: Set = None,
                  logger=None, ignore_tags: list = ["一般"]) -> Author:
    if logger is None:
        logger = get_logger(context="AudienceWorker")
    if author is None:
        tmp_id = f"{doc.s_area_id}-{doc.author}"
        author = Author(id_=tmp_id, name=doc.author, s_area_id=doc.s_area_id)
    results = audience_model.predict([doc], bypass_labels=bypass_labels)
    rs, prob = results
    if rs is not None and prob is not None and\
       rs[0][0] is not None and prob[0][0][0] is not None:
        # fixme 等mongodb支援完成後調整儲存格式
        for label, prob_ in zip(rs, prob):
            if isinstance(label, tuple):
                for l_, p_ in prob_:
                    if l_ not in ignore_tags:
                        author.add_label(doc_id=doc.id_, label=l_, predict_result=p_,
                                         model_type=audience_model.model_type, model_name=audience_model.name)
                        author.add_content(label=l_, content=doc.content)
            else:
                for l_, p_ in prob_:
                    if label == l_ and label not in ignore_tags:
                        author.add_label(doc_id=doc.id_, label=label, predict_result=p_,
                                         model_type=audience_model.model_type, model_name=audience_model.name)
                        author.add_content(label=label, content=doc.content)
    return author


def run_labeling(models: List[AudienceModel], docs: Iterable,
                 init_author: dict = None, quick_mode=False, logger=None, ignore_tags: list = ["一般"]) \
        -> Dict[str, Author]:
    if logger is None:
        logger = get_logger(context="AudienceWorker")
    author_dict = init_author if init_author is not None else dict()
    for doc in tqdm(docs, desc=f"Predicting documents, models={[model.name for model in models]}"):
        tmp_id = f"{doc.s_area_id}_{doc.author}"
        author = author_dict.get(tmp_id, Author(id_=tmp_id, name=doc.author, s_area_id=doc.s_area_id))
        for model in models:
            author = _run_labeling(model, doc, author, bypass_labels=author.get_labels() if quick_mode else None,
                                   ignore_tags=ignore_tags)
            author_dict[author.id_] = author
            if author.docs:
                break
    return author_dict
