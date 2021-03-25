from django.urls import path

from . import views

app_name = 'labeling_jobs'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.LabelingJobDetailView.as_view(), name='labeling-job-detail'),
    path('create/', views.LabelingJobCreate.as_view(), name='labeling-job-create'),
    path('<int:pk>/update/', views.LabelingJobUpdate.as_view(), name='labeling-job-update'),
    path('<int:pk>/delete/', views.LabelingJobDelete.as_view(), name='labeling-job-delete'),
    path('<int:pk>/documents', views.LabelingJobDocumentsView.as_view(), name="labeling-job-docs"),
]
