from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'modeling_jobs'
urlpatterns = [
    path('', views.IndexAndCreateView.as_view(), name='index'),
    path('<int:pk>/', views.JobDetailAndUpdateView.as_view(), name='job-detail'),
    path('create', views.JobCreateView.as_view(), name='job-create'),
    path('<int:pk>/update', views.JobUpdateView.as_view(), name='job-update'),
    path('<int:pk>/delete', views.JobDeleteView.as_view(), name='job-delete'),
    path('<int:model_id>/delete', views.doc_delete, name='api-doc-delete'),
    path('<int:model_id>/update', views.doc_update, name='api-doc-update'),
    path('createTask', views.create_task, name='api-doc-create'),
    path('updateTask', views.update_task, name='api-doc-update'),
    path('deleteTask', views.delete_task, name='api-doc-delete'),
    path('insert_csv', views.insert_csv, name='api-doc-insert_csv'),
    path('<int:pk>/training', views.training_model, name='training-model'),
    path('<int:job_id>/import', views.UploadModelJobCreate.as_view(), name='import-model'),
    path('<int:pk>/ext_test', views.testing_model_via_ext_data, name='api-ext-testing-model'),
    path('<int:modeling_job_id>/result_page', views.result_page, name='api-doc-result-page'),
    path('api/<int:pk>/progress', views.get_progress, name='api-job-progress'),
    # report curd
    path('<int:job_id>/report/<int:pk>', views.ReportDetail.as_view(), name="report-detail"),

    # term weight curd
    path('<int:job_id>/term_weight/add', views.TermWeightCreate.as_view(), name="term-weight-add"),
    path('<int:job_id>/term_weight/<int:pk>/update', views.TermWeightUpdate.as_view(), name="term-weight-update"),
    path('<int:job_id>/term_weight/<int:pk>/delete', views.TermWeightDelete.as_view(), name="term-weight-delete"),

]

# rest-framework settings

router = routers.DefaultRouter()
router.register(r'jobs', views.JobViewSet)
router.register(r'terms', views.TermWrightViewSet)
# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns += [
    path('apis/jobs/<int:pk>', views.JobViewSet.as_view({'get': 'list'}), name='modelingjob-detail'),
    path('apis/jobs/<int:job_id>/terms', views.TermWrightViewSet.as_view({'get': 'list'}), name='term-weight-list'),
    # path('apis/jobs/<int:job_id>/terms/<int:pk>', views.TermWrightViewSet.as_view({'get': 'detail'}),
    #      name='term-weight-detail'),
    path('apis/', include(router.urls)),
    path('apis/api-auth/', include('rest_framework.urls', namespace='rest_framework'))

]
