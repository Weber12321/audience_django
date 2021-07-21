# Audience Toolkits Django version

## requirements
- python 3.7+
- mysql

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

## available models
### Supervise Models
#### SVM
待補充
#### RandomForest
待補充
### RuleBase Models
#### Keyword
待補充
#### Regex
待補充

## available features
- 待補充
- 待補充
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
首先先嘗試：
```shell
python manage.py makemigrations --merge
```
若還是無法解決， 可嘗試的修正方式為重新命名資料表（與程式需求一致），或者可參考以下方法重建資料表：
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

### 如何使用Apple silicon機器開發
由於部分套件尚未支援arm64環境，需使用rosetta 2轉譯的方式模擬intel x86_64執行python，詳細可參考 [這篇](https://www.caktusgroup.com/blog/2021/04/02/python-django-react-development-apple-silicon/) 的方式安裝python，並使用模擬的python執行檔建立venv即可。
> 若您的terminal是使用zsh，請確認是否支援rosetta 2轉譯，建議使用文中的方式使用bash。