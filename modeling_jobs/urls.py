from django.urls import path

from . import views

app_name = 'modeling_jobs'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.modelInfoView.as_view(), name='model_info'),
    # path('<int:pk>/delete', views.docDeleteView.as_view(), name='doc-delete'),
    path('<int:model_id>/delete', views.docDelete, name='api-doc-delete'),
    path('<int:model_id>/update', views.docUpdate, name='api-doc-update'),
    path('createTask', views.createTask, name='api-doc-create'),
    path('updateTask', views.updateTask, name='api-doc-update'),
    path('deleteTask', views.deleteTask, name='api-doc-delete'),
    path('insert_csv', views.insert_csv, name='api-doc-insert_csv'),
    path('training_model', views.training_model, name='api-doc-training-model'),
    path('testing_model', views.testing_model, name='api-doc-testing-model'),
    path('<int:modeling_job_id>/result_page', views.result_page, name='api-doc-result-page'),
]
