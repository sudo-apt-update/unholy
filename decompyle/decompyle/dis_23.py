"""Disassembler of Python byte code into mnemonics."""

import sys
import types

from opcode_25 import *
from opcode_25 import __all__ as _opcodes_all

__all__ = ["dis","disassemble","distb","disco"] + _opcodes_all
del _opcodes_all

def dis(x=None):
    """Disassemble classes, methods, functions, or code.

    With no argument, disassemble the last traceback.

    """
    if x is None:
        distb()
        return
    if type(x) is types.InstanceType:
        x = x.__class__
    if hasattr(x, 'im_func'):
        x = x.im_func
    if hasattr(x, 'func_code'):
        x = x.func_code
    if hasattr(x, '__dict__'):
        items = x.__dict__.items()
        items.sort()
        for name, x1 in items:
            if type(x1) in (types.MethodType,
                            types.FunctionType,
                            types.CodeType,
                            types.ClassType):
                print "Disassembly of %s:" % name
                try:
                    dis(x1)
                except TypeError, msg:
                    print "Sorry:", msg
                print
    elif hasattr(x, 'co_code'):
        disassemble(x)
    elif isinstance(x, str):
        disassemble_string(x)
    else:
        raise TypeError, \
              "don't know how to disassemble %s objects" % \
              type(x).__name__

def distb(tb=None):
    """Disassemble a traceback (default: last traceback)."""
    if tb is None:
        try:
            tb = sys.last_traceback
        except AttributeError:
            raise RuntimeError, "no last traceback to disassemble"
        while tb.tb_next: tb = tb.tb_next
    disassemble(tb.tb_frame.f_code, tb.tb_lasti)

def disassemble(co, lasti=-1):
    """Disassemble a code object."""
    code = co.co_code

    byte_increments = [ord(c) for c in co.co_lnotab[0::2]]
    line_increments = [ord(c) for c in co.co_lnotab[1::2]]
    table_length = len(byte_increments) # == len(line_increments)

    lineno = co.co_firstlineno
    table_index = 0
    while (table_index < table_length
           and byte_increments[table_index] == 0):
        lineno += line_increments[table_index]
        table_index += 1
    addr = 0
    line_incr = 0

    labels = findlabels(code)
    n = len(code)
    i = 0
    extended_arg = 0
    free = None
    while i < n:
        c = code[i]
        op = ord(c)

        if i >= addr:
            lineno += line_incr
            while table_index < table_length:
                addr += byte_increments[table_index]
                line_incr = line_increments[table_index]
                table_index += 1
                if line_incr:
                    break
            else:
                addr = sys.maxint
            if i > 0:
                print
            print "%3d"%lineno,
        else:
            print '   ',

        if i == lasti: print '-->',
        else: print '   ',
        if i in labels: print '>>',
        else: print '  ',
        print `i`.rjust(4),
        print opname[op].ljust(20),
        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i+1])*256 + extended_arg
            extended_arg = 0
            i = i+2
            if op == EXTENDED_ARG:
                extended_arg = oparg*65536L
            print `oparg`.rjust(5),
            if op in hasconst:
                print '(' + `co.co_consts[oparg]` + ')',
            elif op in hasname:
                print '(' + co.co_names[oparg] + ')',
            elif op in hasjrel:
                print '(to ' + `i + oparg` + ')',
            elif op in haslocal:
                print '(' + co.co_varnames[oparg] + ')',
            elif op in hascompare:
                print '(' + cmp_op[oparg] + ')',
            elif op in hasfree:
                if free is None:
                    free = co.co_cellvars + co.co_freevars
                print '(' + free[oparg] + ')',
        print

def disassemble_string(code, lasti=-1, varnames=None, names=None,
                       constants=None):
    labels = findlabels(code)
    n = len(code)
    i = 0
    while i < n:
        c = code[i]
        op = ord(c)
        if op == opmap['SET_LINENO'] and i > 0:
            print # Extra blank line
        if i == lasti: print '-->',
        else: print '   ',
        if i in labels: print '>>',
        else: print '  ',
        print `i`.rjust(4),
        print opname[op].ljust(15),
        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i+1])*256
            i = i+2
            print `oparg`.rjust(5),
            if op in hasconst:
                if constants:
                    print '(' + `constants[oparg]` + ')',
                else:
                    print '(%d)'%oparg,
            elif op in hasname:
                if names is not None:
                    print '(' + names[oparg] + ')',
                else:
                    print '(%d)'%oparg,
            elif op in hasjrel:
                print '(to ' + `i + oparg` + ')',
            elif op in haslocal:
                if varnames:
                    print '(' + varnames[oparg] + ')',
                else:
                    print '(%d)' % oparg,
            elif op in hascompare:
                print '(' + cmp_op[oparg] + ')',
        print

disco = disassemble                     # XXX For backwards compatibility

def findlabels(code):
    """Detect all offsets in a byte code which are jump targets.

    Return the list of offsets.

    """
    labels = []
    n = len(code)
    i = 0
    while i < n:
        c = code[i]
        op = ord(c)
        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i+1])*256
            i = i+2
            label = -1
            if op in hasjrel:
                label = i+oparg
            elif op in hasjabs:
                label = oparg
            if label >= 0:
                if label not in labels:
                    labels.append(label)
    return labels


def _test():
    """Simple test program to disassemble a file."""
    if sys.argv[1:]:
        if sys.argv[2:]:
            sys.stderr.write("usage: python dis.py [-|file]\n")
            sys.exit(2)
        fn = sys.argv[1]
        if not fn or fn == "-":
            fn = None
    else:
        fn = None
    if fn is None:
        f = sys.stdin
    else:
        f = open(fn)
    source = f.read()
    if fn is not None:
        f.close()
    else:
        fn = "<stdin>"
    code = compile(source, fn, "exec")
    dis(code)

if __name__ == "__main__":
    _test()