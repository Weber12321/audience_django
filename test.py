# from pathlib import Path
#
# import environ
#
#
# BASE_DIR = Path(__file__).resolve().parent
#
# env = environ.Env()
# env.read_env((BASE_DIR / '.env').open())
# # read from .env
# DATABASES = {
#     'default': {
#         'ENGINE': env("DATABASE_ENGINE"),
#         'NAME': env("DATABASE_NAME"),  # 目標資料庫的名稱
#         'USER': env("DATABASE_USER"),  # 資料庫帳號
#         'PASSWORD': env("DATABASE_PASSWORD"),  # 資料庫密碼
#         'HOST': env("DATABASE_HOST"),  # 主機位置，可以先測本地localhost
#         'PORT': env("DATABASE_PORT"),
#     }
# }
#
# print(DATABASES)


# modify the predict task

# from predicting_jobs.tasks import call_check_status
# import requests
#
# from audience_toolkits.settings import API_PATH
#
# check_status_path = f'{API_PATH}/api/tasks/{"9014b13653e111ecb688d45d6456a14d"}'
# api_headers = {
#     'accept': 'application/json',
# }
#
# r = requests.get(check_status_path, headers=api_headers)
#
#
# check_status_result = r.json()
# print(check_status_result['error_message']['prod_stat'])

# def predict_task(job: PredictingJob, predicting_target: PredictingTarget,
#                  model_type: str = 'keyword_model', predict_type: str = 'author_name',
#                  output_db = 'audience_result'):
#
#     job.job_status = JobStatus.PROCESSING
#     job.save()
#
#     source: Source = predicting_target.sour
#     ce
#
#     api_path = f'{API_PATH}/api/tasks/'
#
#     api_headers = API_HEADERS
#
#     api_request_body = {
#         "MODEL_TYPE": model_type,
#         "PREDICT_TYPE": predict_type,
#         "START_TIME": f"{predicting_target.begin_post_time}",
#         "END_TIME": f"{predicting_target.end_post_time}",
#         "INPUT_SCHEMA": source.schema,
#         "INPUT_TABLE": source.tablename,
#         "OUTPUT_SCHEMA": output_db,
#         "COUNTDOWN": 5,
#         "SITE_CONFIG": {"host": source.host,
#                         "port": source.port,
#                         "user": source.username,
#                         "password": source.password,
#                         'db': source.schema,
#                         'charset': 'utf8mb4'}
#     }
#
#     try:
#         predicting_target.job_status = JobStatus.PROCESSING
#         predicting_target.save()
#         r = requests.post(api_path, headers=api_headers, data=json.dumps(api_request_body))
#
#         logger.info(f"Status:{r.status_code},{r.json()}")
#         if r.status_code != 200:
#             predicting_target.job_status = JobStatus.ERROR
#
#
#         # predicting_target.job_status = JobStatus.DONE
#         # predicting_target.save()
#
#         # if success
#         # job.job_status = JobStatus.DONE
#     # except TaskCanceledByUserException as e:
#     #     job.error_message = "Job canceled by user."
#     #     job.job_status = JobStatus.BREAK
#     except Exception as e:
#         # if something wrong
#         logger.error(e)
#         job.error_message = e
#         job.job_status = JobStatus.ERROR
#     finally:
#         job.save()
# def get_temp_rule(applying_models: List[ApplyingModel]) -> List[Dict]:\

# job = PredictingJob.objects.get(pk=13)
# applying_models = job.applyingmodel_set.order_by("priority", "created_at")
#
# model_list = []
#
# for applying_model in applying_models:
#     if applying_model.modeling_job.model_name.lower() == 'regex_model':
#         model = get_model(applying_model.modeling_job)
#         # print(model.model_dir_name)
#         if model.patterns:
#             model_list.append(dict(model.patterns))
#     if applying_model.modeling_job.model_name.lower() == 'keyword_model':
#         model = get_model(applying_model.modeling_job)
#         # print(model.model_dir_name)
#         if model.rules:
#             model_list.append(dict(model.rules))
#
# print(model_list)
    # return model_list

