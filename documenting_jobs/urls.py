from django.urls import path, include

from . import views

app_name = 'documenting_jobs'
urlpatterns = [
    # task crud
    path('', views.render_index, name='index'),
    # sample_file
    path('add', views.task_create, name='doc-add'),
    path('sample', views.download_sample_file, name='sample-download'),
    path('<str:task_id>', views.render_detail, name='job-detail'),
    path('<str:task_id>/description', views.task_description, name='job-description'),
    # document crud
    path('<str:task_id>/update', views.task_update, name='doc-update'),
    path('<str:task_id>/delete', views.task_delete, name='doc-delete'),
    path('<str:task_id>/rules/add', views.add_rule, name='rule-add'),
    path('<str:task_id>/dataset/<int:dataset_id>/update', views.update_data, name='dataset-update'),
    path('<str:task_id>/rules/<int:rule_id>/update', views.update_rule, name='rule-update'),
    path('<str:task_id>/dataset/<int:dataset_id>/delete', views.delete_data, name='dataset-delete'),
    path('<str:task_id>/rules/<int:rule_id>/delete', views.delete_rule, name='rule-delete'),
    # upload / download
    path('<str:task_id>/upload', views.upload_file, name='dataset-upload'),
    path('<str:task_id>/download', views.post_download_file, name='dataset-download'),
    path('<str:task_id>/download/get', views.get_download_file, name='get-download-file'),
]
