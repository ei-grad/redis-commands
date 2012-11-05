#!/usr/bin/env python

import rules

from nose.tools import eq_


def test_formatter():
    eq_(rules.formatter('%.6d')(1), '000001')


def test_mapper():
    def f(a):
        return a + 1
    eq_(rules.mapper(f)(range(5)), range(1, 6))


def test_indent_for():
    eq_(rules.indent_for(['a']), ['    a'])


def test_composition():

    def f1(a):
        return a + 1

    def f2(a):
        return a * 2

    eq_(rules.composition(f1, f2)(1), 3)


N1 = {"name": "ip:port", "type": "string"}
N2 = {"name": "serialized-value", "type": "string"}

def test_name():
    eq_(rules.name(N1), 'ip_port')
    eq_(rules.name(N2), 'serialized_value')

def test_getname_to():

    def f1(a):
        eq_(a, 'ip:port')

    rules.getname_to(f1)(N1)

    def f2(a):
        eq_(a, 'serialized-value')

    rules.getname_to(f2)(N2)


CMDARG = {'command': 'AGGREGATE'}

def test_subcommand_name():
    eq_(rules.subcommand_name(CMDARG), 'aggregate')


def test_for_loop():
    eq_(rules.for_loop('a', 'l', ['print(a)']), [
        "for a in l:",
        "    print(a)"
    ])


LISTARG = {'name': ['a', 'b']}

def test_join_listarg():
    eq_(rules.join_listarg(LISTARG), 'a, b')


LIMIT = {"command": "LIMIT",
         "name": ["offset", "count"],
         "type": ["integer", "integer"],
         "optional": True}

def test_for_listarg_subcommand():
    eq_(rules.for_listarg_subcommand(LIMIT, ['print(offset, count)']), [
        "for offset, count in limit:",
        "    print(offset, count)"
    ])


BY = {"command": "BY",
      "name": "pattern",
      "type": "pattern",
      "optional": True}

def test_for_singlearg_subcommand():
    eq_(rules.for_singlearg_subcommand(BY, ['print(pattern)']), [
        "for pattern in by:",
        "    print(pattern)"
    ])


def test_args_append():
    eq_(rules.args_append('a-1'), 'args.append(a_1)')


def test_args_extend():
    eq_(rules.args_extend('a-1'), 'args.extend(a_1)')


def test_args_append_subcommand():
    eq_(rules.args_append_subcommand(BY), 'args.append("BY")')


def test_args_append_listarg():
    eq_(rules.args_append_listarg(LIMIT), [
        "args.append(offset)",
        "args.append(count)"
    ])


def test_expand_listarg_subcommand():
    eq_(rules.expand_listarg_subcommand(LIMIT), "offset, count = limit")


GET = {"command": "GET",
       "name": "pattern",
       "type": "string",
       "optional": True,
       "multiple": True}

def test_if_subcommand():
    eq_(rules.if_subcommand(BY, ['print(by)']), [
        'if by:',
        '    print(by)'
    ])


WEIGHTS = {"command": "WEIGHTS",
           "name": "weight",
           "type": "integer",
           "variadic": True,
           "optional": True}

def test_variadic():
    eq_(rules.variadic(WEIGHTS, ['print(weights)']), [
        'if weights:',
        '    args.append("WEIGHTS")',
        '    print(weights)'
    ])
