import logging
from pathlib import Path


def configurar_log(pasta: str = "logs") -> logging.Logger:
    Path(pasta).mkdir(exist_ok=True)
    log = logging.getLogger("accessflow.rpa")
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    for h in (logging.FileHandler(Path(pasta) / "rpa.log", encoding="utf-8"),
              logging.StreamHandler()):
        h.setFormatter(fmt)
        log.addHandler(h)
    return log
