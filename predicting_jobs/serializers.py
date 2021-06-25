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
    feature = serializers.SerializerMethodField(read_only=True)

    def get_feature(self, result: PredictingResult):
        return result.applied_model.feature if result.applied_model else "UNK"

    class Meta:
        model = PredictingResult
        fields = ['id',
                  'source_author',
                  'data_id',
                  'label_name',
                  # 'score',
                  'applied_model',
                  'feature',
                  'applied_content',
                  'applied_meta',
                  'created_at']
