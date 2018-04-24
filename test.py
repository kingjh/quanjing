# -*- coding: utf-8 -*-
import time
import re

s = '\u963f\u5c14\u4f2f\u7279xb7\u7231\u56e0\u65af\u5766\xa0xa0'
s1 = "".join(re.split(r"\xa0|x[a|b][0|7]|U0.{7}", s))
print(s1)
