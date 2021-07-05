from rest_framework import serializers

from modeling_jobs.models import ModelingJob, TermWeight


class JobSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="modeling_jobs:modelingjob-detail")
    created_by = serializers.StringRelatedField()
    jobRef = serializers.HyperlinkedIdentityField(view_name="labeling_jobs:job-detail")

    # termweights = serializers.HyperlinkedRelatedField(view_name='modeling_jobs:termweight-detail', many=True,
    #                                                   read_only=True)

    class Meta:
        model = ModelingJob
        # fields = ['url', 'id', 'name', 'created_at', 'created_by']
        fields = '__all__'
        # fields = [
        #     "id",
        #     "url",
        #     "created_by",
        #     "name",
        #     "description",
        #     "is_multi_label",
        #     "model_name",
        #     "feature",
        #     "job_status",
        #     "error_message",
        #     "ext_test_status",
        #     "model_path",
        #     "created_at",
        #     "jobRef",
        #     "termweights",
        # ]


class TermWeightSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="modeling_jobs:termweight-detail")
    modeling_job = serializers.HyperlinkedRelatedField(view_name="modeling_jobs:modelingjob-detail", read_only=True)
    label = serializers.StringRelatedField()
    label_id = serializers.StringRelatedField()

    class Meta:
        model = TermWeight
        fields = ['url', 'id', 'term', 'label', 'label_id', 'weight', 'modeling_job']
        # fields = "__all__"
