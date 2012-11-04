#!/usr/bin/env python
# coding: utf-8


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

argname = lambda x: x.lower().replace('-', '_').replace(':', '_')

indent = lambda i: '    %s' % i
indent_for = lambda l: map(indent, l)
indent_if = lambda l: map(indent, l)

name = lambda arg: argname(arg['name'])
subcommand_name = lambda arg: argname(arg['command'])

for_loop = lambda iterator, collection, body: [
    'for %s in %s:' % (iterator, collection)
] + indent_for(body)

join_listarg = lambda arg: ', '.join([argname(i) for i in arg['name']])

for_listarg = lambda arg, collection, body: for_loop(
    join_listarg(arg), collection, body
)
for_singlearg = lambda arg, collection, body: for_loop(
    name(arg), collection, body
)

def for_subcommand(func):
    return lambda arg: func(arg, subcommand_name(arg))
for_listarg_subcommand = for_subcommand(for_listarg)
for_singlearg_subcommand = for_subcommand(for_singlearg)

args_append = lambda x: 'args.append(%s)' % argname(x)
args_extend = lambda x: 'args.extend(%s)' % argname(x)
args_append_subcommand = lambda arg: 'args.append("%s")' % arg['command']
args_append_listarg = lambda arg: [args_append(i) for i in arg['name']]

expand_listarg_subcommand = lambda arg: '%s = %s' % (
    join_listarg(arg), subcommand_name(arg)
)

if_passed = lambda var, body: [
    'if len(%s):' % var
] + indent_if(body)
if_passed_subcommand = lambda arg, body: if_passed(
    subcommand_name(arg), body
)
variadic = lambda arg, body: if_passed_subcommand(arg,
    [args_append_subcommand(arg)] + body
)

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
                args_extend(arg['command'])
            )
        )
    ],

    [
        [subcommand, optional, listarg],
        lambda arg: if_passed_subcommand(
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
