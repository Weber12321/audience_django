import json

from django.contrib.auth.models import User, Group
from rest_framework import serializers

from modeling_jobs.models import ModelingJob
from predicting_jobs.models import PredictingJob, PredictingResult, PredictingTarget, ApplyingModel


class TargetSerializer(serializers.ModelSerializer):
    results = serializers.HyperlinkedIdentityField(lookup_field='id', lookup_url_kwarg='target_id',
                                                   view_name='predicting_jobs:target-results')

    class Meta:
        model = PredictingTarget
        fields = [
            "id",
            "name",
            "description",
            "begin_post_time",
            "end_post_time",
            "min_content_length",
            "max_content_length",
            "job_status",
            "error_message",
            "predicting_job",
            "source",
            "results"
        ]
    # todo 如何設定label


class ApplyingModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplyingModel
        fields = "__all__"


class JobSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="predicting_jobs:predictingjob-detail")
    predictingtarget_set = TargetSerializer(many=True, read_only=True)
    applyingmodel_set = ApplyingModelSerializer(many=True, read_only=True)

    class Meta:
        model = PredictingJob
        fields = ['url', 'id', 'name', 'created_at', 'created_by', 'applyingmodel_set', 'predictingtarget_set']


class ResultSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    applied_feature = serializers.CharField(source='get_applied_feature_display')
    applied_meta = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    # applied_model = serializers.StringRelatedField()
    model_meta = serializers.SerializerMethodField()
    applied_model_url = serializers.HyperlinkedRelatedField(
        many=False,
        read_only=True,
        view_name='modeling_jobs:job-detail'
    )

    def get_model_meta(self, result: PredictingResult):
        modeling_job = result.applied_model
        return {
            "name": modeling_job.name,
            "model_type": modeling_job.model_name
        }

    def get_applied_meta(self, result: PredictingResult):
        if result.applied_model.model_name == "term_weight_model":
            return result.applied_meta
        else:
            return result.applied_meta

    class Meta:
        model = PredictingResult
        # fields = "__all__"
        fields = [
            'id',
            'source_author',
            'data_id',
            'label_name',
            'applied_model',
            'applied_feature',
            'applied_content',
            'applied_meta',
            'created_at',
            'model_meta',
            'applied_model_url',
        ]
