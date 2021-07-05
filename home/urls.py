from django.urls import path, include

from rest_framework import routers
from . import views

app_name = 'home'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
]

# rest-framework settings

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns += [
    path('apis/', include(router.urls)),
    path('apis/api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
