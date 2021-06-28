import json

from django.contrib.auth.models import User, Group
from rest_framework import serializers

from predicting_jobs.models import PredictingJob, PredictingResult, PredictingTarget, ApplyingModel


class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictingTarget
        fields = "__all__"
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
