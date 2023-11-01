[![CICD](https://github.com/skiloop/okutils/actions/workflows/code.yml/badge.svg)](https://github.com/sharkdp/fd/actions/workflows/CICD.yml)
okutils
===== 
a python utils

# Document

## mp_append_log

append log to file, multiple process supported

```python
from okutils.tools import mp_append_log

mp_append_log("debug.log", "welcome")
```