from django.urls import path

from . import views

app_name = 'labeling_jobs'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.LabelingJobDetailView.as_view(), name='job-detail'),
    path('create/', views.LabelingJobCreate.as_view(), name='job-create'),
    path('<int:pk>/update/', views.LabelingJobUpdate.as_view(), name='job-update'),
    path('<int:pk>/delete/', views.LabelingJobDelete.as_view(), name='job-delete'),
    path('<int:pk>/documents', views.LabelingJobDocumentsView.as_view(), name="job-docs"),
    path('<int:job_id>/file/upload/', views.UploadFileJobCreate.as_view(), name='upload-job-create'),
    path('<int:job_id>/file/<int:pk>/delete/', views.UploadFileJobDelete.as_view(), name='upload-job-delete'),
]
