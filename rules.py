#!/usr/bin/env python
# coding: utf-8

import json
from functools import partial
from operator import itemgetter
import os
import sys


formatter = partial(partial, str.__mod__)
mapper = partial(partial, map)
indent = formatter('    %s')
indent_if = mapper(indent)
indent_for = indent_if

def argname(x):
    return x.lower().replace('-', '_').replace(':', '_')

def composition(func1, func2):
    def inner(*args, **kwargs):
        return func1(func2(*args, **kwargs))
    return inner

argname_from = partial(composition, argname)
getname = itemgetter('name')
name = argname_from(getname)
subcommand_name = argname_from(itemgetter('command'))

def for_loop(iterator, collection, body):
    return [
        'for %s in %s:' % (iterator, collection)
    ] + indent_for(body)

joiner = partial(partial, str.join)
join_listarg = composition(joiner(', '), composition(mapper(argname), getname))

def for_listarg(arg, collection, body):
    return for_loop(join_listarg(arg), collection, body)

def for_singlearg(arg, collection, body):
    return for_loop(name(arg), collection, body)

def for_subcommand(func):
    def _inner_for_subcommmand(arg, body):
        return func(arg, subcommand_name(arg), body)
    return _inner_for_subcommmand

for_listarg_subcommand = for_subcommand(for_listarg)
for_singlearg_subcommand = for_subcommand(for_singlearg)

scoremember_name = formatter('member_score_dict')
items = formatter('%s.items()')

def for_scoremember(func):
    def _inner_for_scoremember(arg, body):
        return func(arg, items(scoremember_name(arg)), body)
    return _inner_for_scoremember
for_listarg_scoremember = for_scoremember(for_listarg)

args_append = formatter('args.append(%s)')
args_extend = formatter('args.extend(%s)')
args_append_name = composition(args_append, name)
args_append_subcommand = composition(formatter('args.append("%s")'),
                                     itemgetter('command'))

args_append_listarg = composition(
    mapper(composition(args_append, argname)), getname
)

def expand_listarg_subcommand(arg):
    return '%s = %s' % (join_listarg(arg), subcommand_name(arg))

def if_len(var, body):
    return ['if len(%s):' % var] + indent_if(body)

def if_subcommand(arg, body):
    return ['if %s:' % subcommand_name(arg)] + indent_if(body)

def variadic(arg, body):
    return if_subcommand(arg, [args_append_subcommand(arg)] + body)


def has(field):
    return lambda cmd, arg: field in arg

def equal(field, value):
    return lambda cmd, arg: arg.get(field) == value

def isinst(field, value):
    return lambda cmd, arg: isinstance(arg.get(field), value)


subcommand = has('command')
multiple = equal('multiple', True)
listarg = isinst('name', list)
singlearg = isinst('name', basestring)
is_variadic = equal('variadic', True)
optional = equal('optional', True)
numkeys = equal('name', 'numkeys')
scoremember = equal('name', ['score', 'member'])

CODE_RULES = [

    [
        [subcommand, multiple, listarg],
        lambda arg: for_listarg_subcommand(
            arg, [
                args_append_subcommand(arg)
            ] + args_append_listarg(arg)
        )
    ],

    [
        [subcommand, multiple, singlearg],
        lambda arg: for_singlearg_subcommand(
            arg, [args_append_subcommand(arg), args_append_name(arg)]
        )
    ],

    [
        [subcommand, is_variadic, listarg],
        lambda arg: variadic(
            arg, for_listarg_subcommand(
                arg, args_append_listarg(arg)
            )
        )
    ],


    [
        [subcommand, is_variadic, singlearg],
        lambda arg: variadic(
            arg, for_singlearg_subcommand(arg,
                [args_extend(subcommand_name(arg))]
            )
        )
    ],

    [
        [subcommand, optional, listarg],
        lambda arg: if_subcommand(
            arg, [
                args_append_subcommand(arg),
                expand_listarg_subcommand(arg),
            ] + args_append_listarg(arg)
        )
    ],
    [
        [numkeys],
        lambda arg: [args_append('len(keys)')]
    ],
    [
        [listarg, multiple, scoremember],
        lambda arg: for_listarg_scoremember(arg, args_append_listarg(arg))
    ],
]

ARGS = {}
CODE = {}
DOCS = {}

def get_commands(fname):
    return json.load(open(fname))


if __name__ == "__main__":
    import logging
    fname = os.path.join(os.path.dirname(__file__), 'commands.json')
    commands = get_commands(fname)
    for cmd, params in sorted(commands.items()):
        if 'arguments' in params:
            for arg in params['arguments']:
                for flt, action in CODE_RULES:
                    if all(i(cmd, arg) for i in flt):
                        sys.stdout.write('Code for %s:%s\n' % (cmd, arg))
                        sys.stdout.write('\n'.join(action(arg)))
                        sys.stdout.write('\n\n')
                        break
                else:
                    pass
                    #logging.error("no code rule for %s:%s", cmd, getname(arg))
        else:
            pass
            #logging.error('no arguments for %s', cmd)
