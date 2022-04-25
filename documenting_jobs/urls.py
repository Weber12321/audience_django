from django.urls import path, include

from . import views

app_name = 'documenting_jobs'
urlpatterns = [
    # task crud
    path('', views.IndexAndCreateView.as_view(), name='index'),
    path('<int:pk>/', views.DetailAndUpdateView.as_view(), name='job-detail'),
    path('<int:pk>/delete/', views.JobDeleteView.as_view(), name='job-delete'),
    # document crud
    path('<int:pk>/document/add', views.document_create, name='doc-add'),
    path('<int:pk>/document/render', views.document_render, name='doc-render'),
    path('<int:pk>/document/update', views.document_update, name='doc-update'),
    path('<int:pk>/document/delete', views.document_delete, name='doc-delete'),
    # upload / download
    path('<int:pk>/upload', views.upload_file, name='doc-upload'),
    path('<int:pk>/download', views.download_file, name='doc-download')
]
