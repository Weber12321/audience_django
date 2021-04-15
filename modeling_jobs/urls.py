from django.urls import path

from . import views

app_name = 'modeling_jobs'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('create', views.JobCreateView.as_view(), name='job-create'),
    path('<int:pk>/update', views.JobUpdateView.as_view(), name='job-update'),
    path('<int:pk>/delete', views.JobDeleteView.as_view(), name='job-delete'),
    path('<int:model_id>/delete', views.doc_delete, name='api-doc-delete'),
    path('<int:model_id>/update', views.doc_update, name='api-doc-update'),
    path('createTask', views.create_task, name='api-doc-create'),
    path('updateTask', views.update_task, name='api-doc-update'),
    path('deleteTask', views.delete_task, name='api-doc-delete'),
    path('insert_csv', views.insert_csv, name='api-doc-insert_csv'),
    path('training_model', views.training_model, name='api-doc-training-model'),
    path('testing_model', views.testing_model, name='api-doc-testing-model'),
    path('<int:modeling_job_id>/result_page', views.result_page, name='api-doc-result-page'),
]
