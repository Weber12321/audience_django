from django.urls import path, include

from . import views

app_name = 'documenting_jobs'
urlpatterns = [
    # task crud
    path('', views.render_index, name='index'),
    path('<str:task_id>', views.render_detail, name='job-detail'),
    # path('', views.IndexAndCreateView.as_view(), name='index'),
    # path('<int:pk>/', views.DetailAndUpdateView.as_view(), name='job-detail'),
    # path('<int:pk>/delete/', views.JobDeleteView.as_view(), name='job-delete'),
    # # document crud
    path('/add', views.task_create, name='doc-add'),
    path('<str:task_id>/update', views.task_update, name='doc-update'),
    path('<str:task_id>/delete', views.task_delete, name='doc-delete'),
    # path('<str:task_id>/document/render', views.task_render, name='doc-render'),
    # path('<str:task_id>/dataset/<int:dataset_id>/update', views.update_data, name='dataset-update'),
    path('<str:task_id>/rules/<int:rule_id>/update', views.update_rule, name='rule-update'),
    path('<str:task_id>/document/<int:dataset_id>/delete', views.task_delete, name='dataset-delete'),
    # # upload / download
    path('<str:task_id>/upload', views.upload_file, name='dataset-upload'),
    path('<str:task_id>/download', views.post_download_file, name='dataset-download')
]
