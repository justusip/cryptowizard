from markets.markets import Markets
from misc.schedule import Schedule


class Program:
    def __init__(self):
        self.schedules = []
        pass

    def every(self, func, days=0, hours=0, minutes=0, seconds=0):
        self.schedules.append(Schedule(
            days * 24 * 60 * 60 + hours * 60 * 60 + minutes * 60 + seconds,
            func
        ))

    async def run_schedules(self, *args, **kwargs):
        for schedule in self.schedules:
            await schedule.run_schedule(*args, **kwargs)

    async def init(self, markets: Markets):
        pass

    async def loop(self, markets: Markets):
        pass
