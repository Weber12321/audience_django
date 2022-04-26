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
    path('<str:task_id>/document/render', views.task_render, name='doc-render'),
    path('<str:task_id>/document/update', views.task_update, name='doc-update'),
    path('<str:task_id>/document/delete', views.task_delete, name='doc-delete'),
    # # upload / download
    path('<int:pk>/upload', views.upload_file, name='doc-upload'),
    path('<int:pk>/download', views.post_download_file, name='doc-download')
]
