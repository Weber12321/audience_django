import json

from django import template

from modeling_jobs.models import ModelingJob
from predicting_jobs.models import PredictingTarget

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_apply_path_features(json_str):
    apply_path = []
    for model in json.loads(json_str):
        model_path: str = model.get('model', "unk")
        model_id = model_path.split('_')[0]
        try:
            modeling_job = ModelingJob.objects.get(pk=model_id)
        except:
            modeling_job = None
        apply_path.append(
            {"model": modeling_job, "feature": model.get('feature'), "content": model.get('value')})

    return apply_path
