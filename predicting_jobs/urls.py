from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'predicting_jobs'
urlpatterns = [
    path('', views.IndexAndCreateView.as_view(), name='index'),
    path('<int:pk>/', views.PredictingJobDetailAndUpdateView.as_view(), name='job-detail'),
    path('create/', views.PredictingJobCreate.as_view(), name='job-create'),
    path('<int:pk>/update/', views.PredictingJobUpdate.as_view(), name='job-update'),
    path('<int:pk>/delete/', views.PredictingJobDelete.as_view(), name='job-delete'),
    path('<int:pk>/run/', views.start_job, name='start-job'),
    path('<int:pk>/cancel/', views.cancel_job, name='cancel-job'),

    # targets
    path('<int:job_id>/target/add', views.PredictingTargetCreate.as_view(), name='job-target-add'),
    path('<int:job_id>/target/<int:pk>/update', views.PredictingTargetUpdate.as_view(), name='job-target-update'),
    path('<int:job_id>/target/<int:pk>/delete', views.PredictingTargetDelete.as_view(), name='job-target-delete'),
    path('<int:job_id>/target/<int:pk>/result_samples', views.PredictResultSamplingListView.as_view(),
         name='result-samples'),

    # applying models
    path('<int:job_id>/applying-model/add', views.ApplyingModelCreate.as_view(), name='job-applying-model-add'),
    path('<int:job_id>/applying-model/<int:pk>/update', views.ApplyingModelUpdate.as_view(),
         name='job-applying-model-update'),
    path('<int:job_id>/applying-model/<int:pk>/delete', views.ApplyingModelDelete.as_view(),
         name='job-applying-model-delete'),

    # apis
    path('api/<int:pk>/progress', views.get_progress, name='api-job-progress'),
]

# rest-framework settings

router = routers.DefaultRouter()
router.register(r'jobs', views.JobViewSet)
router.register(r'targets', views.TargetViewSet)
router.register(r'applying_models', views.ApplyingModelViewSet)
router.register(r'results', views.ResultViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns += [
    # path('apis/targets/<int:target_id>/results', views.ResultViewSet.as_view({'get': 'list'}), name='target-results'),
    path('apis/', include(router.urls)),
    path('apis/api-auth/', include('rest_framework.urls', namespace='rest_framework'))

]
