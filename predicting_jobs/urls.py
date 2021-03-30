from django.urls import path

from . import views

app_name = 'predicting_jobs'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.PredictingJobDetailView.as_view(), name='job-detail'),
    path('create/', views.PredictingJobCreate.as_view(), name='job-create'),
    path('<int:pk>/update/', views.PredictingJobUpdate.as_view(), name='job-update'),
    path('<int:pk>/delete/', views.PredictingJobDelete.as_view(), name='job-delete'),
    path('<int:job_id>/target/add', views.PredictingTargetCreate.as_view(), name='job-target-add'),
    path('<int:job_id>/target/<int:pk>/update', views.PredictingTargetUpdate.as_view(), name='job-target-update')
]
