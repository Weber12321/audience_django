from . import views

from django.contrib.auth import views as auth_views
from django.urls import path, include

app_name = 'labeling_jobs'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('create/', views.JobCreate.as_view(), name='job-create'),
    path('<int:pk>/update/', views.JobUpdate.as_view(), name='job-update'),
    path('<int:pk>/delete/', views.JobDelete.as_view(), name='job-delete'),
    path('<int:pk>/documents', views.JobDocumentsView.as_view(), name="job_docs")
]
