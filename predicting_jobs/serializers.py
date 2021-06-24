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
    apply_path = serializers.SerializerMethodField(read_only=False)

    def get_apply_path(self, result):
        return json.loads(result.apply_path)

    class Meta:
        model = PredictingResult
        fields = "__all__"
