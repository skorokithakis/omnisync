"""A progress indicator and remaining time calculator class."""
import time

def timetostr(duration):
    """Convert seconds to D:H:M:S format (whichever applicable)."""
    duration = int(duration)
    timelist = [duration / 86400, (duration / 3600) % 24]
    timestring = ""
    printall = False
    for item in timelist:
        printall |= item
        if printall:
            timestring += str(item).zfill(2) + ":"
    timestring += str((duration / 60) % 60).zfill(2) + ":" + str(duration % 60).zfill(2)
    return timestring


class Progress:
    """Track the progress of an operation and calculate the projected time to
    its completion."""
    def __init__(self, totalitems, timeasstring = True):
        """Create a Progress instance. totalitems must be the total number of
        items we intend to process, so the class knows how far we've gone."""
        self._totalitems = totalitems
        self._starttime = time.time()
        self._timeasstring = timeasstring

    def progress(self, itemnumber):
        """We have progressed itemnumber items, so return our completion
        percentage, items/total items, total time and projected total
        time."""
        elapsed = time.time() - self._starttime
        # Multiply by 1.0 to force conversion to long.
        percentcomplete = (1.0 * itemnumber) / self._totalitems
        try:
            total = int(elapsed / percentcomplete)
        except ZeroDivisionError:
            total = 0
        if self._timeasstring:
            return ({"elapsed_time": timetostr(elapsed),
                    "total_time": timetostr(total),
                    "percentage": int(percentcomplete * 100),
                    "item": itemnumber,
                    "items": self._totalitems})
        else:
            return ({"elapsed_time": int(elapsed),
                    "total_time": int(total),
                    "percentage": int(percentcomplete * 100),
                    "item": itemnumber,
                    "items": self._totalitems})

    def progressstring(self, itemnumber):
        """Return a string detailing the current progress."""
        timings = self.progress(itemnumber)
        if itemnumber == self._totalitems:
            return "Done in %s, processed %s items.        \n" % (timings[0], timings[4])
        else:
            return "Progress: %s/%s, %s%%, %s/%s items.\r" % timings
