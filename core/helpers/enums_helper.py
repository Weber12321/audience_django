from enum import IntEnum, Enum


class DBType(Enum):
    MARIADB = "mariadb"
    MONGODB = "mongodb"
    SQLITE = "sqlite"


class Errors(Enum):
    UNKNOWN_DB_TYPE = "Unknown database type."
    UNKNOWN_PREDICT_TARGET_TYPE = "Unknown predict target type."


class PredictTarget(Enum):
    CONTENT = "content"
    AUTHOR_NAME = "author_name"
    S_AREA_ID = "s_area_id"


class ModelType(Enum):
    PROB_MODEL = "prob_model"
    RULE_MODEL = "rule_model"
    KEYWORD_MODEL = "keyword_model"
    RF_MODEL = "rf_model"
    SVM_MODEL = "svm_model"
    XGBOOST_MODEL = "xgboost_model"


class SourceType(Enum):
    DATABASE = "database"
    LOCAL_FILE = "local_file"


class KeywordMatchType(Enum):
    PARTIALLY = "partially"
    ABSOLUTELY = "absolutely"
    START = "start"
    END = "end"


class TokenizerType(Enum):
    DEEPNLP = "deepnlp"
    JIEBA = "jieba"


class ErrorCodes(IntEnum):
    # https://developer.mozilla.org/zh-TW/docs/Web/HTTP/Status
    OK = 200
    DATA_FORMAT_ERROR = 300
    INDEX_ERROR = 301
    FILE_NOT_FOUND = 302
    FUNCTION_NOT_ALLOWED = 403
    FUNCTION_NOT_FOUND = 404
    INVALID_API_INPUT = 441
    INTERNAL_SERVER_ERROR = 500


class ModelName(Enum):
    RuleModel = "RuleModel"
    KeywordModel = "KeywordModel"
    ProbModel = "ProbModel"
    RFModel = "RFModel"
    SvmModel = "SvmModel"
    XgboostModel = "XgboostModel"


class TaskStatus(Enum):
    WAIT = "wait"
    PROCESSING = "processing"
    BREAK = "break"
    ERROR = "error"
    DONE = "done"


class FileSourceType(Enum):
    FORUM = "討論區"
    SOCIAL = "社群網站"
    COMMENT = "評論"
    QA = "問答網站"
    BLOG = "部落格"
    NEWS = "新聞"
