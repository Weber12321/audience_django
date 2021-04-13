#!/usr/bin/python
# -*- coding: utf-8 -*-
""" A temporary helper that should be merged with text_preprocessor.py
"""
import re
from typing import List, Pattern, Iterable


class REText(object):
    ptt_pattern = r"※\s*?發信站:\s*?批踢踢實業坊\(ptt\.cc\),\s*?來自:\s*?\d+\.\d+\.\d+\.\d+"
    ptt_device_pattern = r"-*?Sent\s*?from.*"
    html_code_pattern = r"&[a-z]+;"
    http_pattern = r"https?://(www.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"
    no_http_url_pattern = r"[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"
    user_pattern = r"[A-Za-z]+\d+|\d+[A-Za-z]+"
    not_chinese_pattern = r"[^\u4e00-\u9fa5\d]+"
    space_pattern = r"^ | $"
    br_pattern = r"(<? ?[bB][rR] ?>?)"


def half2full(txt: str):
    code_base = 65248
    code_start = 65281 - code_base
    code_end = 65374 - code_base
    ss = []
    for s in txt:
        rstring = ""
        for uchar in s:
            inside_code = ord(uchar)
            if code_start <= inside_code <= code_end:
                # 半形字元（除空格）根據關係轉化, e.g., '!'→'！', '~'→'～', 'A'→'Ａ'...
                inside_code += code_base
            else:
                pass
            rstring += chr(inside_code)
        ss.append(rstring)
    return "".join(ss)


def full2half(txt: str):
    ss = []
    for s in txt:
        rstring = ""
        for uchar in s:
            inside_code = ord(uchar)
            if inside_code == 12288:
                # 全形空格 ('　') 直接轉換
                inside_code = 32
            elif 65281 <= inside_code <= 65374:
                # 全形字元根據關係轉化, e.g., '！'→'!', '～'→'~', 'Ａ'→'A'..., 但 '。' 不轉換
                inside_code -= 65248
            else:
                pass
            rstring += chr(inside_code)
        ss.append(rstring)
    return "".join(ss)


def remove_punctuation(txt: str) -> str:
    """
    移除標點符號, 但不包含中文的標點符號
    (如 <>?,./:";'{}[]+-=)(*&^%$#@!~`，。？：；『「」、＋—）＝（＊＆︿％＄＃＠！～)
    @param txt: 文字
    @return: 處理後文字
    """
    txt = re.sub(r"[^\w\s]", "", txt)
    return txt


def full2half_upper2lower(text_lst: List[str]):
    return [full2half(t).lower() for t in text_lst]


def init_patterns() -> List[Pattern]:
    compiled_patterns = []
    patterns = [
        REText.http_pattern, REText.no_http_url_pattern,
        REText.ptt_device_pattern, REText.ptt_pattern,
        REText.br_pattern
    ]
    for pattern in patterns:
        compiled_patterns.append(re.compile(pattern))
    return compiled_patterns


def full2half_noise2empty(
        text_lst: List[str], compiled_patterns: List[Pattern]
) -> List[str]:
    processed_text_lst = []
    for text in text_lst:
        text = full2half(text)
        for pattern in compiled_patterns:
            text = re.sub(pattern, "", text)
        processed_text_lst.append(text)
    return processed_text_lst


def normalize_newlines(text: str) -> str:
    tmp_result = re.sub(REText.br_pattern, "\n", text)
    result = re.sub(r"[\r\n]+", "\n", tmp_result)
    return result


def split_batch(docs: Iterable[str], batch=100) -> Iterable[str]:
    """
    照文章數量分割請求
    Args:
        docs: 所有文章
        batch: 每份數量

    Returns: 分割後文章

    """
    _docs = []
    for doc in docs:
        _docs.append(doc)
        if len(_docs) == batch:
            yield _docs
            _docs.clear()
    yield _docs
