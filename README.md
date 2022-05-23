# Audience Toolkits Django v1.3

###### updated by Weber Huang 2022-05-23

## Workflow

![](C:\Users\ychuang\PycharmProjects\audience-toolkit-dango\audience_site.png)

## Requirements

- python 3.7+
- mysql

## Usage

### Installation

```shell
git clone https://gitting.eland.com.tw/rd2/audience/audience-toolkit-dango.git
cd <project name>
```

### Initial databases

```shell
python manage.py makemigrations <app_name>
python manage.py migrate
```

### Run service

```shell
# 本地端測試站台，服務IP為 127.0.0.1:5000
make run_server_local
# 遠端機部署站台，服務IP為 172.18.20.190:5000
make run_server_remote
# 終端機測試
make run_shell
```

you can manage the command in [Makefile](https://gitting.eland.com.tw/rd2/audience/audience-toolkit-dango/-/blob/master/Makefile)

## For developers
> ### 開發原則
> 避免後續程式測試的困難，請務必注意以下原則：
> - 於django專案目錄中，請盡量並正確使用django內建物件與方法，可以解省很多時間，並且避免很多常見的開發麻煩。（如template中，所有的網址請使用 `{% url %}` tag）
> - `type hint`是好東西，若情況允許請多使用。
> - 所有List或QuerySet避免使用index取值，避免可讀性差造成人為錯誤。
> - 可以的話盡量抽象化程式邏輯，減少人為錯誤與增加可讀性。

### django framwork
You can read and learn everything in [documents](https://docs.djangoproject.com/zh-hans/3.1/).

### template
We use [SB Admin 2](https://startbootstrap.com/previews/sb-admin-2) bootstrap 4.6.0 template (You can find files in `/static/`).

### django rest-framework
- 為Django內的框架`rest-framework`，提供完整的CRUD功能
- 以labeling_jobs api為例子，labeling_jobs app前綴為`labeling_jobs/`，labeling_jobs api前綴為`apis/labeling_jobs/`，完整的網址為`http://127.0.0.1:8000/audience/labeling_jobs/apis/labeling_jobs/`
- 該功能需要使用者登入後，才能正常操作，假設使用postman進行呼叫需在Authorization內增加`Basic Auth`的`Username`、`Password`
- 增加欄位`"name"、"description"、"is_multi_label"、"job_data_type"`

| api_path | params | method | action | return |
|----------|--------|--------|--------|--------|
| audience/labeling_jobs/apis/labeling_jobs/ | | GET | 取回所有資料 | 回傳DB內所有labeling_jobs | 
| audience/labeling_jobs/apis/labeling_jobs/ | 增加欄位 | POST | 新增資料 | 回傳DB內所有labeling_jobs | 
| audience/labeling_jobs/apis/labeling_jobs/1/ | 要更改的欄位 | PUT | 修改該筆ID內的資料 | 回傳該筆資料修改後狀況 | 
| audience/labeling_jobs/apis/labeling_jobs/1/ | | DELETE | 依照該筆ID刪除資料| | 


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

### (fields.E180) SQLite does not support JSONFields.
當執行`python manage.py migrate`時，有機會在`windows`發生，解決辦法可參考[這](https://stackoverflow.com/questions/62637458/django-3-1-fields-e180-sqlite-does-not-support-jsonfields)
> - Check your python installation - is it 32bit or 64bit? run: `python -c "import platform;print(platform.architecture()[0])"`
> - Download the [precompiled DLL](https://www.sqlite.org/download.html)
> - Rename (or delete) sqlite3.dll inside the DLLs directory(`C:\Users\<username>\AppData\Local\Programs\Python\Python37\DLLs`).
> - Now, the JSON1 extension should be ready to be used in Python and Django.

### IntegrityError: UNIQUE constraint failed
當使用API進行DB update時，沒注意到內容重複，會導致資料新增不進去，以至於噴出這個錯誤
> todo: 進行防呆處理 
