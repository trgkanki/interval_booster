from .resource import getResourcePath

from datetime import datetime


fp = None


def log(s: str) -> None:
    global fp

    if not fp:
        now = datetime.now()  # current date and time
        fp = open(getResourcePath("../induction_booster.log"), "a", encoding="utf-8")
        fp.write("\n======= %s =======\n" % now.strftime("%m/%d/%Y, %H:%M:%S"))

    fp.write("%s\n" % s)
    fp.flush()
