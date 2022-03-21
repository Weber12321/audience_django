from django.urls import path, include
from rest_framework import routers
from rest_framework.documentation import include_docs_urls

from . import views

app_name = 'labeling_jobs'
urlpatterns = [
    path('', views.IndexAndCreateView.as_view(), name='index'),
    path('<int:pk>/', views.LabelingJobDetailAndUpdateView.as_view(), name='job-detail'),
    path('<int:pk>/delete/', views.LabelingJobDelete.as_view(), name='job-delete'),
    path('<int:pk>/documents', views.LabelingJobDocumentsView.as_view(), name="job-docs"),
    path('document/<int:pk>', views.DocumentDetailView.as_view(), name="doc-detail"),
    path('<int:pk>/labeling', views.LabelingRandomDocumentView.as_view(), name="job-labeling"),
    path('<int:job_id>/labeling/set_labels', views.doc_label_update, name="set-labels"),
    path('<int:pk>/file/upload/', views.UploadFileJobCreate.as_view(), name='upload-job-create'),
    path('file/<int:pk>/delete/', views.UploadFileJobDelete.as_view(), name='upload-job-delete'),
    # label crud
    path('<int:job_id>/label/add', views.LabelCreate.as_view(), name="labels-add"),
    path('label/<int:pk>', views.LabelDetail.as_view(), name="labels-detail"),
    path('label/<int:pk>/update', views.LabelUpdate.as_view(), name="labels-update"),
    path('label/<int:pk>/delete', views.LabelDelete.as_view(), name="labels-delete"),
    # rule crud
    path('rule/add', views.RuleCreate.as_view(), name="rule-add"),
    path('label/<int:label_id>/rule/add', views.RuleCreate.as_view(), name="label-rule-add"),
    path('rule/<int:pk>/update', views.RuleUpdate.as_view(), name="rule-update"),
    path('rule/<int:pk>/delete', views.RuleDelete.as_view(), name="rule-delete"),
    # func
    path('<int:job_id>/generate_dataset', views.generate_dataset, name="generate-dataset"),

    # sample data
    path('sample_data', views.SampleDataListView.as_view(), name='sample-data-list'),
    path('sample_data/download/<int:sample_data_id>', views.download_sample_data, name='download-sample-data')
]


# rest-framework settings

router = routers.DefaultRouter()
router.register("jobs", views.LabelingJobsSet)
router.register("labels", views.LabelSet)
router.register("rules", views.RuleSet)
router.register("upload_file_jobs", views.UploadFileJobSet)
router.register("documents", views.DocumentSet)

urlpatterns += [
    path('api/jobs', views.LabelingJobsSet.as_view({'get': 'list'}), name='api-job-detail'),
    path('api/labels', views.LabelSet.as_view({'get': 'list'}), name='api-label-detail'),
    path('api/rules', views.RuleSet.as_view({'get': 'list'}), name='api-rule-detail'),
    path('api/documents', views.DocumentSet.as_view({'get': 'list'}), name='api-document-detail'),
    path('api/', include(router.urls)),
    path('api/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
