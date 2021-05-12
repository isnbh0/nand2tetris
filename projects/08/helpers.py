import typing as t


def inc_sp(res):
    res += ["@SP", "M=M+1"]


def dec_sp(res):
    res += ["@SP", "M=M-1"]


def deref_ptr(res, op="D=M"):
    res += ["A=M", op]


def binop(command: str) -> t.List[str]:
    """
    add, sub, and, or
    """

    def execute_binop(res, command):
        d = {"add": "D+M", "sub": "M-D", "and": "D&M", "or": "D|M"}
        deref_ptr(res, f"M={d[command]}")

    res = []
    dec_sp(res)
    deref_ptr(res)
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
        deref_ptr(res, f"D=M-D")
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
    deref_ptr(res)
    dec_sp(res)
    execute_compare(res, command, s)
    return res


def unop(command: str) -> t.List[str]:
    """
    neg, not
    """

    def execute_unop(res, command):
        d = {"neg": "-M", "not": "!M"}
        deref_ptr(res, f"M={d[command]}")

    res = []
    dec_sp(res)
    execute_unop(res, command)
    inc_sp(res)
    return res


def _push_d(res):
    res += ["@SP"]
    deref_ptr(res, op="M=D")
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
    deref_ptr(res, op="D=M")


def pop_argument(index: int):
    res = [f"@{index}", "D=A", "@ARG", "D=D+M", "@addr", "M=D"]
    _pop_to_d(res)
    res += ["@addr"]
    deref_ptr(res, op="M=D")
    return res


def pop_local(index: int):
    res = [f"@{index}", "D=A", "@LCL", "D=D+M", "@addr", "M=D"]
    _pop_to_d(res)
    res += ["@addr"]
    deref_ptr(res, op="M=D")
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
    deref_ptr(res, op="M=D")
    return res


def pop_that(index: int):
    res = [f"@{index}", "D=A", "@THAT", "D=D+M", "@addr", "M=D"]
    _pop_to_d(res)
    res += ["@addr"]
    deref_ptr(res, op="M=D")
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
    deref_ptr(res, op="M=D")
    return res


def assign_label(label: str):
    res = [f"({label})"]
    return res


def goto_label(label: str):
    res = [f"@{label}", "0;JMP"]
    return res


def if_goto_label(label: str):
    res = []
    _pop_to_d(res)
    res += [f"@{label}", "D;JNE"]
    return res
