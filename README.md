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

### API文件
- 以postman為例，以下的API接口都需要在Authorization Type: Basic Auth進行使用者驗證

#### Labeling_jobs

##### LabelingJob

<details>
<summary>LabelingJob(GET)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/labeling_job/ |
    | method | GET |

- Request: 無

- Response

    | 欄位 | 型別 | 說明 |
    |-----|-----|-----|
    | id | integer | 任務ID |
    | name | string | 標記工作名稱 |
    | description | string | 定義與說明 |
    | is_multi_label | boolean | 是否屬於多標籤 |
    | job_data_type | string | 任務類型 |
    | create_at | time | 建立時間 |
    | update_at | time | 最後更改 |
    | created_by | string | User name |
    | url | string | 查詢該筆資料URL |

- Request Example: 無

- Response Example

```json
{
    "url": "http://127.0.0.1:8000/audience/labeling_jobs/apis/labeling_job/10/",
    "id": 10,
    "created_by": "eddy",
    "name": "test",
    "description": "test",
    "is_multi_label": false,
    "job_data_type": "term_weight",
    "created_at": "2021-07-14T15:56:35.164504",
    "updated_at": "2021-07-14T15:56:35.164504"
}
```

</details>

<details>
<summary>LabelingJob(POST)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/labeling_job/ |
    | method | POST |

- Request

    | 欄位 | 型別 | 必填 | 說明 |
    |-----|-----|------|-----|
    | name | string | Y |標記工作名稱 |
    | description | string | Y |定義與說明 |
    | is_multi_label | boolean | N | 是否屬於多標籤 |
    | job_data_type | string | N | 任務類型 |

- Response

    | 欄位 | 型別 | 說明 |
    |-----|-----|-----|
    | id | integer | 任務ID |
    | name | string | 標記工作名稱 |
    | description | string | 定義與說明 |
    | is_multi_label | boolean | 是否屬於多標籤 |
    | job_data_type | string | 任務類型 |
    | create_at | time | 建立時間 |
    | update_at | time | 最後更改 |
    | created_by | string | User name |
    | url | string | 查詢該筆資料URL |

- Request Example: 

```json
{
    "name": "postman_test",
    "description": "postman_desc",
    "is_multi_label": false,
    "job_data_type": "term_weight"
}
```

- Response Example

```json
{
    "url": "http://127.0.0.1:8000/audience/labeling_jobs/apis/labeling_job/12/",
    "id": 12,
    "created_by": "eddy",
    "name": "postman_test",
    "description": "postman_desc",
    "is_multi_label": false,
    "job_data_type": "term_weight",
    "created_at": "2021-07-16T14:13:37.852387",
    "updated_at": "2021-07-16T14:13:37.852387"
}
```

</details>

<details>
<summary>LabelingJob(PUT)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/labeling_job/{labeling_job id}/ |
    | method | PUT |

- Request: 無

    | 欄位 | 型別 | 必填 | 說明 |
    |-----|-----|------|-----|
    | name | string | Y |標記工作名稱 |
    | description | string | Y |定義與說明 |
    | is_multi_label | boolean | N | 是否屬於多標籤 |
    | job_data_type | string | N | 任務類型 |

- Response

    | 欄位 | 型別 | 說明 |
    |-----|-----|-----|
    | id | integer | 任務ID |
    | name | string | 標記工作名稱 |
    | description | string | 定義與說明 |
    | is_multi_label | boolean | 是否屬於多標籤 |
    | job_data_type | string | 任務類型 |
    | create_at | time | 建立時間 |
    | update_at | time | 最後更改 |
    | created_by | string | User name |
    | url | string | 查詢該筆資料URL |

- Request Example:

```json
{
    "name": "postman_test2",
    "description": "postman_desc2",
    "is_multi_label": true,
    "job_data_type": "regex"
}
```

- Response Example

```json
{
    "url": "http://127.0.0.1:8000/audience/labeling_jobs/apis/labeling_job/10/",
    "id": 10,
    "created_by": "eddy",
    "name": "postman_test2",
    "description": "postman_desc2",
    "is_multi_label": true,
    "job_data_type": "regex",
    "created_at": "2021-07-16T14:13:37.852387",
    "updated_at": "2021-07-16T14:26:49.023896"
}
```

</details>

<details>
<summary>LabelingJob(DEL)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/labeling_job/{labeling_job id}/ |
    | method | DEL |

- Request: 無

- Response: 無

- Request Example: 無

- Response Example: 無

</details>

##### Label

<details>
<summary>Label(GET)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/label/ |
    | method | GET |

- Request: 無

- Response

    | 欄位 | 型別 | 說明 |
    |-----|-----|-----|
    | id | integer | 標籤ID |
    | job | string | 任務名稱 |
    | job_id | integer | 任務ID |
    | name | string | 標籤名稱 |
    | description | string | 標籤定義 |
    | target_amount | integer | 目標數量 |
    | create_at | time | 建立時間 |
    | update_at | time | 最後更改 |
    | url | string | 查詢該筆資料URL |

- Request Example: 無

- Response Example

```json
{
    "url": "http://127.0.0.1:8000/audience/labeling_jobs/apis/label/9/",
    "id": 9,
    "job": "2222 (監督式學習模型資料)",
    "job_id": 2,
    "name": "postman",
    "description": "postman_desc",
    "target_amount": 200,
    "created_at": "2021-07-14T11:32:29.317272",
    "updated_at": "2021-07-14T11:32:29.317272"
}
```

</details>

<details>
<summary>Label(POST)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/label/ |
    | method | POST |

- Request

    | 欄位 | 型別 | 必填 | 說明 |
    |-----|-----|------|-----|
    | job_id | integer | Y | 任務ID |
    | name | string | Y |標記工作名稱 |
    | description | string | Y |定義與說明 |
    | target_amount | integer | N | 目標數量 |

- Response

    | 欄位 | 型別 | 說明 |
    |-----|-----|-----|
    | id | integer | 標籤ID |
    | job | string | 任務名稱 |
    | job_id | integer | 任務ID |
    | name | string | 標籤名稱 |
    | description | string | 標籤定義 |
    | target_amount | integer | 目標數量 |
    | create_at | time | 建立時間 |
    | update_at | time | 最後更改 |
    | created_by | string | User name |
    | url | string | 查詢該筆資料URL |

- Request Example: 

```json
{
    "job_id": 2,
    "name": "postman",
    "description": "postman_desc",
    "target_amount": 200
}
```

- Response Example

```json
{
    "url": "http://127.0.0.1:8000/audience/labeling_jobs/apis/labeling_job/13/",
    "id": 13,
    "created_by": "eddy",
    "name": "postman_test",
    "description": "postman_desc",
    "is_multi_label": false,
    "job_data_type": "term_weight",
    "created_at": "2021-07-16T14:13:37.852387",
    "updated_at": "2021-07-16T14:13:37.852387"
}
```

</details>

<details>
<summary>Label(PUT)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/label/{label id}/ |
    | method | PUT |

- Request: 無

    | 欄位 | 型別 | 必填 | 說明 |
    |-----|-----|------|-----|
    | job_id | integer | Y | 任務ID |
    | name | string | Y |標記工作名稱 |
    | description | string | Y |定義與說明 |
    | target_amount | integer | N | 目標數量 |

- Response

    | 欄位 | 型別 | 說明 |
    |-----|-----|-----|
    | id | integer | 標籤ID |
    | job | string | 任務名稱 |
    | job_id | integer | 任務ID |
    | name | string | 標籤名稱 |
    | description | string | 標籤定義 |
    | target_amount | integer | 目標數量 |
    | create_at | time | 建立時間 |
    | update_at | time | 最後更改 |
    | url | string | 查詢該筆資料URL |

- Request Example:

```json
{
    "job_id": 2,
    "name": "postman26",
    "description": "postman_desc26",
    "target_amount": 200
}
```

- Response Example

```json
{
    "url": "http://127.0.0.1:8000/audience/labeling_jobs/apis/label/13/",
    "id": 13,
    "job": "2222 (監督式學習模型資料)",
    "job_id": 2,
    "name": "postman26",
    "description": "postman_desc26",
    "target_amount": 200,
    "created_at": "2021-07-16T14:36:20.196095",
    "updated_at": "2021-07-16T14:38:58.681244"
}
```

</details>

<details>
<summary>Label(DEL)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/label/{label id}/ |
    | method | DEL |

- Request: 無

- Response: 無

- Request Example: 無

- Response Example: 無

</details>

##### Rule

<details>
<summary>Rule(GET)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/rule/ |
    | method | GET |

- Request: 無

- Response

    | 欄位 | 型別 | 說明 |
    |-----|-----|-----|
    | id | integer | 規則ID |
    | job | string | 任務名稱 |
    | job_id | integer | 任務ID |
    | label | string | 標籤名稱 |
    | label_id | integer | 標籤ID |
    | content | string | 規則內文 |
    | rule_type | string(RuleType) | 規則類型 |
    | match_type | string(MatchType) | 比對方式 |
    | score | float | 命中分數 |
    | create_at | time | 建立時間 |
    | created_by | string | User name |
    | url | string | 查詢該筆資料URL |

- Request Example: 無

- Response Example

```json
{
    "url": "http://127.0.0.1:8000/audience/labeling_jobs/apis/rule/14/",
    "id": 14,
    "job": "男性_作者名關鍵字規則(關鍵字規則模型資料)",
    "job_id": 9,
    "label": "男性",
    "label_id": 22,
    "created_by": "eddy",
    "content": "家豪",
    "rule_type": "keyword",
    "match_type": "start",
    "score": 1.0,
    "created_at": "2021-07-16T11:24:47.316956"
}
```

</details>

<details>
<summary>Rule(POST)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/rule/ |
    | method | POST |

- Request

    | 欄位 | 型別 | 必填 | 說明 |
    |-----|-----|------|-----|
    | job_id | integer | Y | 任務ID |
    | label_id | integer | Y | 標籤ID |
    | content | string | Y | 規則內文 |
    | rule_type | string(RuleType) | N | 規則類型 |
    | match_type | string(MatchType) | N | 比對方式 |
    | score | float | N | 命中分數 |

- Response

    | 欄位 | 型別 | 說明 |
    |-----|-----|-----|
    | id | integer | 規則ID |
    | job | string | 任務名稱 |
    | job_id | integer | 任務ID |
    | label | string | 標籤名稱 |
    | label_id | integer | 標籤ID |
    | content | string | 規則內文 |
    | rule_type | string(RuleType) | 規則類型 |
    | match_type | string(MatchType) | 比對方式 |
    | score | float | 命中分數 |
    | create_at | time | 建立時間 |
    | created_by | string | User name |
    | url | string | 查詢該筆資料URL |

- Request Example: 

```json
{
    "job_id": 9,
    "label_id": 22,
    "content": "志明",
    "rule_type": "keyword",
    "match_type": "end",
    "score": 1.0
}
```

- Response Example

```json
{
    "url": "http://127.0.0.1:8000/audience/labeling_jobs/apis/rule/14/",
    "id": 14,
    "job": "男性_作者名關鍵字規則(關鍵字規則模型資料)",
    "job_id": 9,
    "label": "男性",
    "label_id": 22,
    "created_by": "eddy",
    "content": "志明",
    "rule_type": "keyword",
    "match_type": "end",
    "score": 1.0,
    "created_at": "2021-07-16T11:26:47.316956"
}
```

</details>

<details>
<summary>Rule(PUT)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/rule/{rule id}/ |
    | method | PUT |

- Request: 無

    | 欄位 | 型別 | 必填 | 說明 |
    |-----|-----|------|-----|
    | content | string | Y | 規則內文 |
    | rule_type | string(RuleType) | N | 規則類型 |
    | match_type | string(MatchType) | N | 比對方式 |
    | score | float | N | 命中分數 |

- Response

    | 欄位 | 型別 | 說明 |
    |-----|-----|-----|
    | id | integer | 標籤ID |
    | job | string | 任務名稱 |
    | job_id | integer | 任務ID |
    | name | string | 標籤名稱 |
    | description | string | 標籤定義 |
    | target_amount | integer | 目標數量 |
    | create_at | time | 建立時間 |
    | update_at | time | 最後更改 |
    | url | string | 查詢該筆資料URL |

- Request Example:

```json
{
    "content": "龍尼",
    "rule_type": "keyword",
    "match_type": "end",
    "score": 1.0
}
```

- Response Example

```json
{
    "url": "http://127.0.0.1:8000/audience/labeling_jobs/apis/rule/14/",
    "id": 14,
    "job": "男性_作者名關鍵字規則(關鍵字規則模型資料)",
    "job_id": 9,
    "label": "男性",
    "label_id": 22,
    "created_by": "eddy",
    "content": "龍尼",
    "rule_type": "keyword",
    "match_type": "end",
    "score": 1.0,
    "created_at": "2021-07-16T11:27:47.316956"
}
```

</details>

<details>
<summary>rule(DEL)</summary>

- 獲得所有任務列表

    | 項目 | 說明 |
    |-----|-----|
    | API URL | {domain}/labeling_jobs/apis/rule/{rule id}/ |
    | method | DEL |

- Request: 無

- Response: 無

- Request Example: 無

- Response Example: 無

</details>

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

### (fields.E180) SQLite does not support JSONFields.
當執行`python manage.py migrate`時，有機會在`windows`發生，解決辦法可參考[這](https://stackoverflow.com/questions/62637458/django-3-1-fields-e180-sqlite-does-not-support-jsonfields)
> - Check your python installation - is it 32bit or 64bit? run: `python -c "import platform;print(platform.architecture()[0])"`
> - Download the [precompiled DLL](https://www.sqlite.org/download.html)
> - Rename (or delete) sqlite3.dll inside the DLLs directory(`C:\Users\<username>\AppData\Local\Programs\Python\Python37\DLLs`).
> - Now, the JSON1 extension should be ready to be used in Python and Django.

### IntegrityError: UNIQUE constraint failed
當使用API進行DB update時，沒注意到內容重複，會導致資料新增不進去，以至於噴出這個錯誤
> todo: 進行防呆處理 
