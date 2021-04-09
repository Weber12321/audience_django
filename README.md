# Audience Toolkits Django version

## requirements
- python 3.7+
- Django 3.1

## usage
### initial databases
```shell
python manage.py makemigrations <app_name>
python manage.py migrate
```

### run service
```shell
# 啟動任務管理器
python manage.py qcluster
# 啟動伺服器
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
### 若`makemigrations`時出現找不到資料表錯誤該怎麼辦？
此問題主要是因為資料庫中的資料表有異動造成，或者與model預設的model name對不起來。
修正方式建議為重新命名資料表（與程式需求一致），或者可參考以下方法重建資料表：
1. 先將`<app_name>/migrations`資料夾刪除
1. 將有使用到app資料庫的部分著解掉
   1. `<project_name>/settings.py`中的`INSTALLED_APPS`的admin與其他相關的apps
   2. `<project_name>/urls.py`中註冊的urls
1. 確認有將欲重建的app保留在`<project_name>/settings.py`中的`INSTALLED_APPS`中
1. 執行指令建立資料表
```shell
python manage.py makemigrations <app_name>
python manage.py migrate
```
3. 將前面註解掉的部分取消註解
