import logging
import os
import stat
import tempfile


def remove_readonly(func, path):
    """
    移除唯獨權限，並重新嘗試刪除
    :param func: 刪除function
    :param path: 檔案路徑
    :return:
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def make_temporary_dir(logger: logging, temp_dirname: str) -> str:
    temp_dir = os.path.join(tempfile.gettempdir(), temp_dirname)
    if not os.path.exists(temp_dir):
        try:
            os.makedirs(temp_dir)
            logger.debug(f"Create the directory <{temp_dir}>.")
            return temp_dir
        except Exception as ex:
            logger.error(ex, exc_info=True)
            return tempfile.gettempdir()
    else:
        return temp_dir
