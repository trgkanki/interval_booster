from .resource import getResourcePath

from datetime import datetime


def log(s: str) -> None:
    now = datetime.now()  # current date and time
    with open(getResourcePath("../induction_booster.log"), "a", encoding="utf-8") as f:
        f.write("[%s]\t%s\n" % (now.strftime("%Y-%m-%d %H:%M:%S"), s))
