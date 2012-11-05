#!/usr/bin/env python
# coding: utf-8

from operator import itemgetter
from functools import partial


def has(field):
    return lambda cmd, args: field in args

def equal(field, value):
    return lambda cmd, args: args.get(field) == value

def isinst(field, value):
    return lambda cmd, args: isinstance(args.get(field), value)


subcommand = has('command')
multiple = equal('multiple', True)
listarg = isinst('name', list)
singlearg = isinst('name', basestring)
variadic = equal('variadic', True)
optional = equal('optional', True)

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

getname_to = partial(composition, func2=getname)

def for_loop(iterator, collection, body):
    return [
        'for %s in %s:' % (iterator, collection)
    ] + indent_for(body)

joiner = partial(partial, str.join)
join_listarg = composition(joiner(', '), getname_to(mapper(argname)))

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


args_append = composition(formatter('args.append(%s)'), argname)
args_extend = composition(formatter('args.extend(%s)'), argname)
args_append_subcommand = composition(formatter('args.append("%s")'),
                                     itemgetter('command'))

args_append_listarg = getname_to(mapper(args_append))

def expand_listarg_subcommand(arg):
    return '%s = %s' % (join_listarg(arg), subcommand_name(arg))

def if_len(var, body):
    return ['if len(%s):' % var] + indent_if(body)

def if_subcommand(arg, body):
    return ['if %s:' % subcommand_name(arg)] + indent_if(body)

def variadic(arg, body):
    return if_subcommand(arg, [args_append_subcommand(arg)] + body)


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
            arg, [
                args_append_subcommand(arg),
                args_append(arg)
            ]
        )
    ],

    [
        [subcommand, variadic, listarg],
        lambda arg: variadic(
            arg, for_listarg_subcommand(
                arg, args_append_listarg(arg)
            )
        )
    ],


    [
        [subcommand, variadic, singlearg],
        lambda arg: variadic(
            arg, for_singlearg_subcommand(arg,
                args_extend(subcommand_name(arg))
            )
        )
    ],

    [
        [subcommand, optional, listarg],
        lambda arg: if_subcommand(
            arg, [
                args_append_subcommand(arg),
                expand_listarg_subcommand(arg),
                args_append_listarg(arg)
            ]
        )
    ]
]

ARGS = {}
CODE = {}
DOCS = {}
