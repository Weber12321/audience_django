import json

from django import template

from modeling_jobs.models import ModelingJob

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
        modeling_job = ModelingJob.objects.get(pk=model_id)
        apply_path.append(
            f"{modeling_job.name}, {model.get('feature')}, {model.get('value')}")
    return apply_path
