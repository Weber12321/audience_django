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
    path('<int:job_id>/document/<int:pk>', views.DocumentDetailView.as_view(), name="doc-detail"),
    path('<int:pk>/labeling', views.LabelingRandomDocumentView.as_view(), name="job-labeling"),
    path('<int:job_id>/labeling/set_labels', views.doc_label_update, name="set-labels"),
    path('<int:job_id>/file/upload/', views.UploadFileJobCreate.as_view(), name='upload-job-create'),
    path('<int:job_id>/file/<int:pk>/delete/', views.UploadFileJobDelete.as_view(), name='upload-job-delete'),
    # label curd
    path('<int:job_id>/label/add', views.LabelCreate.as_view(), name="label-add"),
    path('<int:job_id>/label/<int:pk>', views.LabelDetail.as_view(), name="label-detail"),
    path('<int:job_id>/label/<int:pk>/update', views.LabelUpdate.as_view(), name="label-update"),
    path('<int:job_id>/label/<int:pk>/delete', views.LabelDelete.as_view(), name="label-delete"),
    # func
    path('<int:job_id>/generate_dataset', views.generate_dataset, name="generate-dataset"),

]
