import json

from django.contrib.auth.models import User, Group
from rest_framework import serializers

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
    applied_model = serializers.HyperlinkedRelatedField(
        many=False,
        read_only=True,
        view_name='modeling_jobs:job-detail'
    )

    def get_applied_meta(self, result: PredictingResult):
        if result.applied_model.model_name == "term_weight_model":
            return json.dumps(result.applied_meta, ensure_ascii=False)
        else:
            return json.dumps(result.applied_meta, ensure_ascii=False)

    class Meta:
        model = PredictingResult
        fields = ['id',
                  'source_author',
                  'data_id',
                  'label_name',
                  'applied_model',
                  'applied_feature',
                  'applied_content',
                  'applied_meta',
                  'created_at']
