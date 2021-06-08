import itertools
import re
import typing as t


def is_generator_empty(generator):
    a, b = itertools.tee(generator)
    try:
        next(a)
    except StopIteration:
        return True, b
    return False, b

token_dict = {
    "keyword": (
        r"class|constructor|function|"
        r"method|field|static|var|"
        r"int|char|boolean|void|true|"
        r"false|null|this|let|do|"
        r"if|else|while|return"
    ),
    "symbol": (
        r"\{|\}|\(|\)|\[|\]|\.|"
        r",|;|\+|\-|\*|/|&|"
        r"\||<|>|=|~"
    ),
    "integerConstant": (
        r"[0-9]|[1-9][0-9]{1,3}|[12][0-9]{4}|"
        r"3[01][0-9]{3}|32[0-6][0-9]{2}|327[0-5][0-9]|3276[0-7]"
    ),
    "stringConstant": r'"[^\"\n]+"',
    "identifier": r"[a-zA-Z_]\w*",
}

token = (
    rf"{token_dict['keyword']}"
    rf"|{token_dict['symbol']}"
    rf"|{token_dict['integerConstant']}"
    rf"|{token_dict['stringConstant']}"
    rf"|{token_dict['identifier']}"
)

token_re = re.compile(token)

def get_token_type(token: str) -> str:
    for k, v in token_dict.items():
        if re.fullmatch(v, token):
            return k
    raise ValueError("Token type not found")

def escape_token(token: str) -> str:
    d_esc = {
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "&": "&amp;",
    }
    if token in d_esc:
        token = d_esc[token]
    return token

def inc_sp(res):
    res += ["@SP", "M=M+1"]


def dec_sp(res):
    res += ["@SP", "M=M-1"]


def deref_m_ptr(res, op="D=M"):
    res += ["A=M", op]


def deref_d_ptr(res, op="D=M"):
    res += ["A=D", op]


def binop(command: str) -> t.List[str]:
    """
    add, sub, and, or
    """

    def execute_binop(res, command):
        d = {"add": "D+M", "sub": "M-D", "and": "D&M", "or": "D|M"}
        deref_m_ptr(res, f"M={d[command]}")

    res = []
    dec_sp(res)
    deref_m_ptr(res)
    dec_sp(res)
    execute_binop(res, command)
    inc_sp(res)
    return res


def compare(command: str, s=0) -> t.List[str]:
    """
    eq, gt, lt
    """

    def execute_compare(res, command, s):
        true = f"TRUE{s}"
        end = f"END{s}"
        d = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}
        deref_m_ptr(res, f"D=M-D")
        # conditional = [f'@{true}', f'D;{d[command]}', 'M=0', f'@{end}', '0;JMP', f'({true})', 'M=-1', f'({end})']
        cond = [
            f"@{true}",
            f"D;{d[command]}",
            "D=0",
        ]  # , 'M=0', f'@{end}', '0;JMP', f'({true})', 'M=-1', f'({end})']
        _push_d(cond)
        cond += [f"@{end}", "0;JMP", f"({true})", "D=-1"]  # , f'({end})']
        _push_d(cond)
        cond += [f"({end})"]

        res += cond

    res = []
    dec_sp(res)
    deref_m_ptr(res)
    dec_sp(res)
    execute_compare(res, command, s)
    return res


def unop(command: str) -> t.List[str]:
    """
    neg, not
    """

    def execute_unop(res, command):
        d = {"neg": "-M", "not": "!M"}
        deref_m_ptr(res, f"M={d[command]}")

    res = []
    dec_sp(res)
    execute_unop(res, command)
    inc_sp(res)
    return res


def _push_d(res):
    res += ["@SP"]
    deref_m_ptr(res, op="M=D")
    inc_sp(res)


def push_constant(index: int) -> t.List[str]:
    res = [f"@{index}", "D=A"]
    _push_d(res)
    return res


def push_argument(index: int) -> t.List[str]:
    res = [f"@{index}", "D=A", "@ARG", "A=D+M", "D=M"]
    _push_d(res)
    return res


def push_local(index: int):
    res = [f"@{index}", "D=A", "@LCL", "A=D+M", "D=M"]
    _push_d(res)
    return res


def push_static(index: int, file_name: str):
    res = [f"@{file_name}.{index}", "D=M"]
    _push_d(res)
    return res


def push_this(index: int):
    res = [f"@{index}", "D=A", "@THIS", "A=D+M", "D=M"]
    _push_d(res)
    return res


def push_that(index: int):
    res = [f"@{index}", "D=A", "@THAT", "A=D+M", "D=M"]
    _push_d(res)
    return res


def push_pointer(index: int):
    if index == 0:
        res = [f"@THIS", "D=M"]
    elif index == 1:
        res = [f"@THAT", "D=M"]
    else:
        raise NotImplementedError
    _push_d(res)
    return res


def push_temp(index: int):
    assert index < 8
    res = [f"@{index}", "D=A", "@5", "A=D+A", "D=M"]
    _push_d(res)
    return res


def _pop_to_d(res):
    dec_sp(res)
    deref_m_ptr(res, op="D=M")


def pop_argument(index: int):
    res = [f"@{index}", "D=A", "@ARG", "D=D+M", "@addr", "M=D"]
    _pop_to_d(res)
    res += ["@addr"]
    deref_m_ptr(res, op="M=D")
    return res


def pop_local(index: int):
    res = [f"@{index}", "D=A", "@LCL", "D=D+M", "@addr", "M=D"]
    _pop_to_d(res)
    res += ["@addr"]
    deref_m_ptr(res, op="M=D")
    return res


def pop_static(index: int, file_name: str):
    res = []
    _pop_to_d(res)
    res += [f"@{file_name}.{index}", "M=D"]
    return res


def pop_this(index: int):
    res = [f"@{index}", "D=A", "@THIS", "D=D+M", "@addr", "M=D"]
    _pop_to_d(res)
    res += ["@addr"]
    deref_m_ptr(res, op="M=D")
    return res


def pop_that(index: int):
    res = [f"@{index}", "D=A", "@THAT", "D=D+M", "@addr", "M=D"]
    _pop_to_d(res)
    res += ["@addr"]
    deref_m_ptr(res, op="M=D")
    return res


def pop_pointer(index: int):
    res = []
    _pop_to_d(res)
    if index == 0:
        res += [f"@THIS", "M=D"]
    elif index == 1:
        res += [f"@THAT", "M=D"]
    else:
        raise NotImplementedError
    return res


def pop_temp(index: int):
    assert index < 8
    res = [f"@{index}", "D=A", "@5", "D=D+A", "@addr", "M=D"]
    _pop_to_d(res)
    res += ["@addr"]
    deref_m_ptr(res, op="M=D")
    return res


def _flabel(label: str, function_name: t.Optional[str]) -> str:
    return f"{label}" if function_name is None else f"{function_name}${label}"


def assign_label(label: str, function_name: t.Optional[str] = None):
    res = [f"({_flabel(label, function_name)})"]
    return res


def goto_label(label: str, function_name: t.Optional[str] = None):
    res = [f"@{_flabel(label, function_name)}", "0;JMP"]
    return res


def if_goto_label(label: str, function_name: t.Optional[str] = None):
    res = []
    _pop_to_d(res)
    res += [f"@{_flabel(label, function_name)}", "D;JNE"]
    return res


def call_function(function_name: str, num_args: int, function_call_counter: int):
    RETURN_ADDRESS = f"return-address{function_call_counter}"
    res = []

    # push return-address
    res += [f"@{RETURN_ADDRESS}", "D=A"]
    _push_d(res)

    # push LCL
    res += ["@LCL", "D=M"]
    _push_d(res)

    # push ARG
    res += ["@ARG", "D=M"]
    _push_d(res)

    # push THIS
    res += ["@THIS", "D=M"]
    _push_d(res)

    # push THAT
    res += ["@THAT", "D=M"]
    _push_d(res)

    # ARG = SP-n-5
    res += ["@SP", "D=M"]
    res += [f"@{num_args}", "D=D-A"]
    res += ["@5", "D=D-A"]
    res += ["@ARG", "M=D"]

    # LCL = SP
    res += ["@SP", "D=M"]
    res += ["@LCL", "M=D"]

    # goto called function
    res += goto_label(label=function_name)

    # assign return address label
    res += assign_label(label=RETURN_ADDRESS)
    return res


def declare_function(function_name: str, num_locals: int):
    res = []
    res += assign_label(f"{function_name}")
    for _ in range(num_locals):
        res += push_constant(0)
    return res


def return_from_function():
    FRAME = "FRAME"
    RET = "RET"
    res = []

    # FRAME = LCL
    res += ["@LCL", "D=M"]
    res += [f"@{FRAME}", "M=D"]

    # RET = *(FRAME-5)
    res += [f"@{FRAME}", "D=M"]
    res += ["@5", "D=D-A"]
    deref_d_ptr(res, op="D=M")
    res += [f"@{RET}", "M=D"]

    # *ARG = pop()
    _pop_to_d(res)
    res += [f"@ARG"]
    deref_m_ptr(res, op="M=D")

    # SP = ARG+1
    res += ["@ARG", "D=M"]
    res += ["@1", "D=D+A"]
    res += ["@SP", "M=D"]

    # THAT = *(FRAME-1)
    res += [f"@{FRAME}", "D=M"]
    res += ["@1", "D=D-A"]
    deref_d_ptr(res, op="D=M")
    res += [f"@THAT", "M=D"]

    # THIS = *(FRAME-2)
    res += [f"@{FRAME}", "D=M"]
    res += ["@2", "D=D-A"]
    deref_d_ptr(res, op="D=M")
    res += [f"@THIS", "M=D"]

    # ARG = *(FRAME-3)
    res += [f"@{FRAME}", "D=M"]
    res += ["@3", "D=D-A"]
    deref_d_ptr(res, op="D=M")
    res += [f"@ARG", "M=D"]

    # LCL = *(FRAME-4)
    res += [f"@{FRAME}", "D=M"]
    res += ["@4", "D=D-A"]
    deref_d_ptr(res, op="D=M")
    res += [f"@LCL", "M=D"]

    # goto *RET
    res += [f"@{RET}"]
    deref_m_ptr(res, op="0;JMP")
    return res


def initialize():
    INIT_CALL = -1
    res = ["// Bootstrap code", "// SP = 256", "// call Sys.init"]

    # SP = 256
    res += ["@256", "D=A"]
    res += [f"@SP", "M=D"]

    # call Sys.init
    res += call_function(
        function_name="Sys.init", num_args=0, function_call_counter=INIT_CALL
    )

    return res


def finish():
    res = ["(END)", "@END", "0;JMP"]
    return res
