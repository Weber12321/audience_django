from . import views

from django.contrib.auth import views as auth_views
from django.urls import path, include

app_name = 'labeling_jobs'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('create', views.create_job, name='create_job'),
]
