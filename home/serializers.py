from django.contrib.auth.models import User, Group
from rest_framework import serializers

from predicting_jobs.models import PredictingJob, PredictingResult


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'groups']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']
