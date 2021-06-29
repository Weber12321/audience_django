from rest_framework import serializers

from modeling_jobs.models import ModelingJob, TermWeight


class JobSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="modeling_jobs:modelingjob-detail")
    created_by = serializers.StringRelatedField()
    terms_url = serializers.HyperlinkedIdentityField(view_name='modeling_jobs:term-weight-list', lookup_field='id',
                                                     lookup_url_kwarg='job_id')

    class Meta:
        model = ModelingJob
        # fields = ['url', 'id', 'name', 'created_at', 'created_by']
        fields = [
            "id",
            "url",
            "created_by",
            "name",
            "description",
            "is_multi_label",
            "model_name",
            "feature",
            "job_status",
            "error_message",
            "ext_test_status",
            "model_path",
            "created_at",
            "jobRef",
            "terms_url"
        ]


class TermWeightSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="modeling_jobs:termweight-detail")
    modeling_job = serializers.HyperlinkedRelatedField(view_name="modeling_jobs:modelingjob-detail", read_only=True)
    label = serializers.CharField()

    class Meta:
        model = TermWeight
        # fields = ['url', 'id', 'name', 'created_at', 'created_by']
        fields = "__all__"
