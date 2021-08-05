class State:
    ok: bool = True

    @staticmethod
    def exit():
        State.ok = False

    @staticmethod
    def ok() -> bool:
        return State.ok
