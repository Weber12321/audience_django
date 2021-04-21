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
> ### 開發原則
> 避免後續程式測試的困難，請務必注意以下原則：
> - `core`資料夾為核心模型相關程式，請勿於此package中使用django的方法與物件。若真的需要請先在django相關程式中將格式處理成python內建物件或方法，再呼叫`core`中的方法或模組。
> - 於django專案目錄中，請盡量並正確使用django內建物件與方法，可以解省很多時間，並且避免很多常見的開發麻煩。（如template中，所有的網址請使用 `{% url %}` tag）
> - `type hint`是好東西，若情況允許請多使用。
> - 所有List或QuerySet避免使用index取值，避免可讀性差造成人為錯誤。
> - 可以的話盡量抽象化程式邏輯，減少人為錯誤與增加可讀性。

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
