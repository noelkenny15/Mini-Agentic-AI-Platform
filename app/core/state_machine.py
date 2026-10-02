from enum import Enum


class State(str, Enum):
    START = "START"
    PLAN = "PLAN"
    INVESTIGATE = "INVESTIGATE"
    PROPOSE = "PROPOSE"
    VERIFY = "VERIFY"
    EXECUTE = "EXECUTE"
    VALIDATE = "VALIDATE"
    COMPLETE = "COMPLETE"
    REJECTED = "REJECTED"


TRANSITIONS = {
    State.START: {State.PLAN},
    State.PLAN: {State.INVESTIGATE},
    State.INVESTIGATE: {State.PROPOSE},
    State.PROPOSE: {State.VERIFY},
    State.VERIFY: {State.EXECUTE, State.REJECTED},
    State.EXECUTE: {State.VALIDATE},
    State.VALIDATE: {State.COMPLETE},
    State.COMPLETE: set(),
    State.REJECTED: set(),
}


def can_transition(current: State, target: State) -> bool:
    return target in TRANSITIONS[current]
