import time


class Schedule:
    def __init__(self, sec, func):
        self.sec = sec
        self.func = func
        self.last_run = None

    async def run_schedule(self, *args, **kwargs):
        cur_time = time.time()
        if self.last_run is not None and cur_time < self.last_run + self.sec:
            return
        self.last_run = cur_time
        await self.func(*args, **kwargs)
