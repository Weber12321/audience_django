# Audience Toolkits Django version

## requirements
- python 3.7+
- Django 3.1

## usage
### initial databases
1. 先將`/audience_toolkits/urls.py`中的`urlpatterns`內容註解掉，避免建立時出現`OperationalError: no such table`錯誤。
```python
# `/audience_toolkits/urls.py`
urlpatterns = [
    # path('', include('home.urls')),
    # path('labeling_jobs/', include('labeling_jobs.urls')),
    # path('modeling_jobs/', include('modeling_jobs.urls')),
    # path('predicting_jobs/', include('predicting_jobs.urls')),
    # path('admin/', admin.site.urls),
    # path('accounts/', include('django.contrib.auth.urls')),
]
```
2. 建立資料表
```shell
python manage.py makemigrations
python manage.py migrate
```
3. 將步驟一註解掉的部分取消註解
```python
# `/audience_toolkits/urls.py`
urlpatterns = [
    path('', include('home.urls')),
    path('labeling_jobs/', include('labeling_jobs.urls')),
    path('modeling_jobs/', include('modeling_jobs.urls')),
    path('predicting_jobs/', include('predicting_jobs.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]
```

### run service
```shell
python manage.py runserver
```

## for developers
### django framwork
You can read and learn everything in [documents](https://docs.djangoproject.com/zh-hans/3.1/).

### template
We use [SB Admin 2](https://startbootstrap.com/previews/sb-admin-2) bootstrap 4.6.0 template (You can find files in `/static/`).

### icons
We use [font-awesome](https://fontawesome.com/icons?d=gallery&p=1&m=free) icons.

## FAQ
