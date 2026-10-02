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
