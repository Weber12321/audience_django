import json

from django_q.tasks import async_task
from rest_framework import serializers

from audience_toolkits.serializers import HyperlinkedRetrieveIdentityField
from labeling_jobs.models import LabelingJob, Label, Rule, UploadFileJob, Document
from labeling_jobs.tasks import import_csv_data_task


class LabelingJobSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    # url = serializers.HyperlinkedIdentityField(view_name="labeling_jobs:job-detail")
    url = HyperlinkedRetrieveIdentityField(view_name="labeling_jobs:job-detail")
    created_by = serializers.StringRelatedField()
    labels = serializers.SerializerMethodField()
    data_type = serializers.CharField(source='get_job_data_type_display')

    class Meta:
        model = LabelingJob
        fields = "__all__"
        # fields = ["id", "name", "description", "is_multi_label",
        #           "job_data_type", "created_at", "updated_at", "created_by"]

    def create(self, validated_data):
        labeling_job = LabelingJob.objects.create(
            created_by=self.context["request"].user,
            **validated_data
        )
        return labeling_job

    def get_labels(self, object):
        labels = object.label_set.values_list(
            "id", "name"
        )
        return [{"id": i, "name": name} for i, name in labels]


class LabelSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = HyperlinkedRetrieveIdentityField(view_name="labeling_jobs:labels-detail")
    update_url = HyperlinkedRetrieveIdentityField(view_name="labeling_jobs:labels-update")
    delete_url = HyperlinkedRetrieveIdentityField(view_name="labeling_jobs:labels-delete")
    # 傳三個引數
    # view_name='test':路由名字,用來反向解析
    # lookup_field='publish_id':要反向解析的引數值
    # lookup_url_kwarg='id':有名分組的名字
    # labeling_job = serializers.HyperlinkedIdentityField(
    #     view_name="labeling_jobs:job-detail",
    #     lookup_field='labeling_job_id',
    #     lookup_url_kwarg="pk",
    # )
    labeling_job = serializers.StringRelatedField()

    # job_id用來指定對應到的job
    labeling_job_id = serializers.IntegerField(label="Job ID", required=True)

    class Meta:
        model = Label
        fields = "__all__"
        # exclude = ["job"]
        # fields = ["id", "job", "name", "description", "target_amount", "job_id"]


class RuleSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = HyperlinkedRetrieveIdentityField(view_name="labeling_jobs:rule-detail")
    labeling_job = serializers.StringRelatedField()
    labeling_job_id = serializers.IntegerField(label="Job ID", required=False)
    label = serializers.StringRelatedField()
    label_id = serializers.IntegerField(label="Label ID", required=False)
    created_by = serializers.StringRelatedField()
    match_type_display = serializers.CharField(source="get_match_type_display")

    class Meta:
        model = Rule
        # fields = ["id", "job", "job_id", "content", "rule_type", "match_type", "score", "created_at", "created_by"]
        fields = "__all__"


class UploadFileJobSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    labeling_job = serializers.StringRelatedField()
    labeling_job_id = serializers.IntegerField(label="Job ID", required=False)
    # jobRef = serializers.HyperlinkedIdentityField(view_name="labeling_jobs:job-detail")
    file = serializers.CharField(label="file")
    created_by = serializers.StringRelatedField()

    class Meta:
        model = UploadFileJob
        fields = "__all__"

    def create(self, validated_data):
        upload_file_job = UploadFileJob.objects.create(
            created_by=self.context["request"].user,
            **validated_data
        )
        async_task(import_csv_data_task, upload_job=upload_file_job, group='upload_documents')
        return upload_file_job


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = HyperlinkedRetrieveIdentityField(view_name="labeling_jobs:document-detail")
    labeling_job = serializers.StringRelatedField()
    labeling_job_id = serializers.IntegerField(label="Labeling Job ID", required=False)

    # labels = serializers.StringRelatedField(many=True)
    labels = LabelSerializer(many=True)
    all_labels = serializers.SerializerMethodField()

    class Meta:
        model = Document
        # fields = ["id", "url", "labeling_job", "labels_name"]
        fields = "__all__"

    def get_all_labels(self, obj):
        all_labels = Label.objects.filter(
            labeling_job_id=obj.labeling_job_id
        ).values_list(
            "id", "name"
        )
        return [{"id": i, "name": name} for i, name in all_labels]
