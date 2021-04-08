import psutil

from core.audience.labeler import run_labeling
from core.dao.audience_task import select_audience_task, update_audience_task_progress_status, \
    update_audience_task_status, \
    AudienceTask
from core.dao.author_example import upsert_authors, upsert_labeling_authors
from core.dao.input_example import get_input_entities_row_count
from core.helpers.data_helpers import DataHelper
from core.helpers.enums_helper import TaskStatus
from core.helpers.log_helper import get_logger
from predicting_jobs.models import PredictingJob


class AudienceWorker:
    def __init__(self, model_list: list, logger=None, task_conn_info=None):
        if logger is None:
            self.logger = get_logger(context="AudienceWorker")
        else:
            self.logger = logger

        self.models = model_list
        self.task_conn_info = task_conn_info

    def run(self, input_data_helper: DataHelper, result_data_helper: DataHelper, document_batch: int = 500,
            fetch_limit_count=-1, author_cache=100):
        authors = dict()

        for docs in input_data_helper.batch_load_examples(batch=document_batch,
                                                          fetch_limit_count=fetch_limit_count):
            authors = run_labeling(models=self.models, docs=docs, init_author=authors, quick_mode=False)
            if len(authors) > author_cache:
                upsert_authors(result_data_helper.get_conn_info(), authors.values())
                authors.clear()
        upsert_authors(result_data_helper.get_conn_info(), authors.values())
        authors.clear()

    def run_labeling(self, input_data_helper: DataHelper, result_data_helper: DataHelper,
                     predicting_job: PredictingJob, document_batch: int = 500,
                     fetch_limit_count=-1, author_cache=100, condition: str = None):
        """
        進行貼標
        :param input_data_helper: 輸入資料源資訊
        :param result_data_helper: 輸出結果資訊
        :param predicting_job: 當前任務
        :param document_batch: 一次抓幾筆任務
        :param fetch_limit_count: 資料源抓取筆數上限
        :param author_cache: 結果cache (如果超過就會先儲存起來)
        :param condition: 查詢資料源sql條件
        :return:
        """
        authors = dict()
        is_first_search = True
        task_id: int = predicting_job.id

        # 取得table總筆數
        total_row_count = fetch_limit_count
        if fetch_limit_count == -1 or fetch_limit_count is None:
            total_row_count = get_input_entities_row_count(conn_info=input_data_helper.get_conn_info(),
                                                           condition=condition)
        self.logger.debug(f"資料explain總筆數:{total_row_count}")

        # 取得該筆任務進度條
        progress_status = predicting_job.progress_status.split("/")
        _start_count = 0 if progress_status[0] == progress_status[1] else int(progress_status[0])
        progress_bar = _start_count  # 初始化計算進度條

        for docs in input_data_helper.batch_load_examples(batch=document_batch,
                                                          fetch_limit_count=fetch_limit_count,
                                                          condition=condition,
                                                          finish_count=_start_count):
            current_db_name = input_data_helper.get_conn_info().schema
            if current_db_name not in predicting_job.progress_db_name:
                predicting_job.progress_db_name.append(current_db_name)

            if not docs:
                if is_first_search:
                    update_audience_task_status(conn_info=self.task_conn_info,
                                                status=TaskStatus.ERROR.value,
                                                task_id=task_id)
                    self.logger.error("找不到相對應的文章")
                else:
                    # 完成任務貼標
                    update_audience_task_progress_status(conn_info=self.task_conn_info,
                                                         progress_db_name=predicting_job.progress_db_name,
                                                         progress_status=f"{progress_bar}/{progress_bar}",
                                                         task_id=task_id)
                    self.logger.debug(f"task id : {task_id}, "
                                      f"source : {input_data_helper.settings['schema']}, 已完成貼標")
                break
            is_first_search = False

            # 檢查是否中斷
            _task = select_audience_task(conn_info=self.task_conn_info, audience_task_id=task_id)
            if _task.status != TaskStatus.PROCESSING.value:
                msg = f"貼標任務中斷, task_id={task_id}, 當前完成筆數={_task.progress_status}"
                self.logger.debug(msg)
                raise TypeError(msg)

            # 顯示當下電腦memory
            progress_bar += len(docs)
            if not progress_bar % 10000:
                self.logger.debug(f"computer used memory:{psutil.virtual_memory().percent}")
                self.logger.debug(f"computer available memory: "
                                  f"{psutil.virtual_memory().available * 100 / psutil.virtual_memory().total}")

            # 進行貼標
            authors = run_labeling(models=self.models, docs=docs, init_author=authors, quick_mode=False)

            # 儲存結果
            if len(authors) > author_cache:
                upsert_labeling_authors(result_data_helper.get_conn_info(), authors.values())
                authors.clear()

            # 更新任務進度
            update_audience_task_progress_status(conn_info=self.task_conn_info,
                                                 progress_db_name=predicting_job.progress_db_name,
                                                 progress_status=f"{progress_bar}/{total_row_count}",
                                                 task_id=task_id)
        # 儲存結果
        upsert_labeling_authors(result_data_helper.get_conn_info(), authors.values())
        authors.clear()

        # 完成任務貼標
        update_audience_task_progress_status(conn_info=self.task_conn_info,
                                             progress_db_name=list(),
                                             progress_status=f"{progress_bar}/{progress_bar}",
                                             task_id=predicting_job._id)

