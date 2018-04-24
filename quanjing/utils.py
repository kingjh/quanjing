# -*- coding: utf-8 -*-
import time
import re

class Utils():
    def get_timestamp():  # 获取当前系统时间戳
        try:
            tamp = time.time()
            timestamp = str(int(tamp)) + "000"
            return timestamp
        except Exception as e:
            print(e)
        finally:
            pass

    def trim_spec_char(s):  # 去掉字符串中的\xa0、xa9、xb0、xb7、emoji (U0xxxxxxx)
        return "".join(re.split(r"\xa0|x[a|b][0|7]|U0.{7}", s))
