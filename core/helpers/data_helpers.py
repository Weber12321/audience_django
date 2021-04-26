import codecs
import csv
from typing import Iterable, List, Dict

import cchardet

from audience_toolkits import settings
from core.dao.input_example import InputExample
from core.helpers.db_helper import get_mysql_connection, select_rows


def get_test_data(file):
    delimiters = [',', '\t']
    encoding = cchardet.detect(file.read())['encoding']
    file.seek(0)
    csv_file = header = None
    for delimiter in delimiters:
        csv_file = csv.DictReader(codecs.iterdecode(file, encoding), skipinitialspace=True,
                                  delimiter=delimiter,
                                  quoting=csv.QUOTE_ALL)
        header = csv_file.fieldnames
        if "content" in header and "label" in header:
            break

    print(header)
    content = []
    labels = []
    # required_fields = ['title', 'author', 's_area_id', 'content', 'label']
    required_fields = ['content', 'label']
    if set(header) != set(required_fields):
        return content, labels
    else:
        for item in csv_file:
            content.append(item.get('content', ''))
            labels.append(item.get('label', ''))
        return content, labels


def get_opview_data_rows(host, port, user, password, source_name, table='ts_page_content', fields: List[str] = None,
                         conditions: List[str] = None, fetch_size: int = 1000, max_rows=None,
                         **kwargs) -> Iterable[Dict]:
    if fields is None:
        fields = ['id', 'content']
    fields_str = ', '.join(fields)
    if conditions is None:
        condition_str = ""
    else:
        condition_str = f" WHERE {' '.join(conditions)}"
    if max_rows:
        limit_str = f" LIMIT {max_rows}"
    else:
        limit_str = ""
    query = f'SELECT {fields_str} FROM `{source_name}`.`{table}`{condition_str}{limit_str};'
    with get_mysql_connection(host, port, user, password, source_name) as connection:
        chunk_rows = select_rows(conn=connection, sql_query=query, fetch_size=fetch_size)
        for rows in chunk_rows:
            for row in rows:
                yield row


def chunks(generator, chunk_size):
    """Yield successive chunks from a generator"""
    chunk = []

    for item in generator:
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = [item]
        else:
            chunk.append(item)

    if chunk:
        yield chunk


if __name__ == '__main__':
    rows = get_opview_data_rows(host="172.18.20.190", port=3306, user='rd2', password='eland4321',
                                source_name="forum_data", fetch_size=23, max_rows=1000,
                                fields=settings.AVAILABLE_FIELDS,
                                conditions=["post_time between '2019-01-01 00:00:00' and '2020-01-01 00:00:00'"])
    count = 0
    for i, row in enumerate(rows):
        print(row)
        count += 1
    print(count)
