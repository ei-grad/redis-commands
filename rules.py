#!/usr/bin/env python
# coding: utf-8

import logging
import json
from functools import partial
from operator import itemgetter
import os
import sys


formatter = partial(partial, str.__mod__)
mapper = partial(partial, map)
indent = mapper(formatter('    %s'))


NAME_MAP = {
    'del': 'delete',
    'exec': 'execute'
}


def argname(x):
    x = x.lower().replace('-', '_').replace(':', '_').replace(' ', '_')
    if x in NAME_MAP:
        x = NAME_MAP[x]
    return x


def composition(func1, func2):
    def composition_inner(*args, **kwargs):
        return func1(func2(*args, **kwargs))
    return composition_inner


argname_from = partial(composition, argname)
getname = itemgetter('name')
name = argname_from(getname)
subcommand_name = argname_from(itemgetter('command'))


def in_list(func):
    def in_list_inner(*args, **kwargs):
        return [func(*args, **kwargs)]
    return in_list_inner


def for_loop(itername, collection, body):
    return [
        'for %s in %s:' % (itername, collection)
    ] + indent(body)


joiner = partial(partial, str.join)
join_listarg = composition(joiner(', '), composition(mapper(argname), getname))


def for_listarg(arg, collection, body):
    return for_loop(join_listarg(arg), collection, body)


def for_singlearg(arg, collection, body):
    return for_loop(name(arg), collection, body)


def for_base(name_getter):
    def for_inner(func):
        def for_inner2(arg, body):
            return func(arg, name_getter(arg), body)
        return for_inner2
    return for_inner

for_subcommand = for_base(subcommand_name)
for_listarg_subcommand = for_subcommand(for_listarg)
for_singlearg_subcommand = for_subcommand(for_singlearg)

joined_listarg_name = composition(joiner('_'), getname)
valuepair_name = composition(formatter("%s_dict"), joined_listarg_name)

for_scoremember = for_base(valuepair_name)
for_listarg_scoremember = for_scoremember(for_listarg)

items = formatter('%s.items()')
for_valuepair = for_base(composition(items, valuepair_name))
for_listarg_valuepair = for_valuepair(for_listarg)

args_append = formatter('args.append(%s)')
args_extend = formatter('args.extend(%s)')
args_append_name = composition(args_append, name)
args_append_subcommand = composition(
    formatter('args.append("%s")'),
    itemgetter('command')
)

args_append_listarg = composition(
    mapper(composition(args_append, argname)),
    getname
)


def fzip(*funcs):
    def fzip_inner(*args, **kwargs):
        return tuple(i(*args, **kwargs) for i in funcs)
    return fzip_inner


expand_listarg_subcommand = composition(
    formatter('%s = %s'),
    fzip(join_listarg, subcommand_name)
)


def if_len(var, body):
    return ['if len(%s):' % var] + indent(body)


def if_subcommand(arg, body):
    return ['if %s:' % subcommand_name(arg)] + indent(body)


def if_arg(arg, body):
    return ['if %s:' % name(arg)] + indent(body)


def variadic(arg, body):
    return if_subcommand(arg, [args_append_subcommand(arg)] + body)


def multname(name):
    if name[-1] == 's':
        return name
    else:
        return '%ss' % name


len1list_name = composition(
    multname,
    composition(
        argname,
        composition(itemgetter(0), getname)
    )
)


def append_if_string_else_extend_base(name_getter):
    def append_if_string_else_extend_base_inner(arg):
        return [
            'if isinstance(%s, basestring):' % name_getter(arg)
        ] + indent([
            args_append(name_getter(arg))
        ]) + [
            'else:'
        ] + indent([
            args_extend(name_getter(arg))
        ])
    return append_if_string_else_extend_base_inner


append_if_string_else_extend = append_if_string_else_extend_base(name)
append_if_string_else_extend_listarg = append_if_string_else_extend_base(len1list_name)

def has(field):
    return lambda cmd, arg: field in arg

def equal(field, value):
    return lambda cmd, arg: arg.get(field) == value

def isinst(field, value):
    return lambda cmd, arg: isinstance(arg.get(field), value)

def second_is_value(cmd, arg):
    return arg['name'][1] == 'value'

def and_(f1, f2):
    def and_inner(*args):
        return f1(*args) and f2(*args)
    return and_inner

def length(item, l):
    def length_inner(cmd, arg):
        return len(arg[item]) == l
    return length_inner


subcommand = has('command')
multiple = equal('multiple', True)
listarg = isinst('name', list)
singlearg = isinst('name', basestring)
is_variadic = equal('variadic', True)
optional = equal('optional', True)
numkeys = equal('name', 'numkeys')
scoremember = equal('name', ['score', 'member'])
valuepair = and_(length('name', 2), second_is_value)


add_eq_none_in_list = in_list(formatter('%s=None'))
name_in_list = in_list(name)
multname_in_list = composition(in_list(multname), name)
opt_name_in_list = composition(in_list(formatter('%s=None')), name)
subcommand_name_in_list = in_list(subcommand_name)
opt_subcommand_name_in_list = composition(in_list(formatter('%s=None')), subcommand_name)
valuepair_name_in_list = in_list(valuepair_name)
len1list_name_in_list = in_list(len1list_name)


RULES = [
    [
        [subcommand, multiple, listarg],
        lambda arg: for_listarg_subcommand(
            arg, [
                args_append_subcommand(arg)
            ] + args_append_listarg(arg)
        ),
        subcommand_name,
    ],
    [
        [subcommand, multiple, singlearg, optional],
        lambda arg: if_subcommand(arg, for_singlearg_subcommand(
            arg, [args_append_subcommand(arg), args_append_name(arg)]
        )),
        opt_subcommand_name_in_list,
    ],
    [
        [subcommand, multiple, singlearg],
        lambda arg: for_singlearg_subcommand(
            arg, [args_append_subcommand(arg), args_append_name(arg)]
        ),
        subcommand_name_in_list,
    ],
    [
        [subcommand, is_variadic, listarg],
        lambda arg: variadic(
            arg, for_listarg_subcommand(
                arg, args_append_listarg(arg)
            )
        ),
        composition(add_eq_none_in_list, subcommand_name),
    ],
    [
        [subcommand, is_variadic, singlearg],
        lambda arg: variadic(arg, [args_extend(subcommand_name(arg))]),
        opt_subcommand_name_in_list,
    ],
    [
        [subcommand, optional, listarg],
        lambda arg: if_subcommand(
            arg, [
                args_append_subcommand(arg),
                expand_listarg_subcommand(arg),
            ] + args_append_listarg(arg)
        ),
        composition(add_eq_none_in_list, subcommand_name),
    ],
    [
        [subcommand, optional, singlearg],
        lambda arg: if_subcommand(
            arg, [
                args_append_subcommand(arg),
                args_append(subcommand_name(arg))
            ]
        ),
        opt_subcommand_name_in_list,
    ],
    [
        [numkeys],
        lambda arg: [args_append('len(keys)')],
        lambda x: [],
    ],
    [
        [listarg, multiple, scoremember],
        lambda arg: for_listarg_scoremember(arg, args_append_listarg(arg)),
        lambda x: ['score_member_dict'],
    ],
    [
        [listarg, valuepair],
        lambda arg: for_listarg_valuepair(arg, args_append_listarg(arg)),
        valuepair_name_in_list,
    ],
    [
        [listarg, length('name', 1)],
        lambda arg: append_if_string_else_extend_listarg(arg),
        len1list_name_in_list,
    ],
    [
        [singlearg, multiple],
        lambda arg: [args_extend(multname(name(arg)))],
        multname_in_list,
    ],
    [
        [singlearg, has('enum'), length('enum', 1), optional],
        lambda arg: if_arg(arg, [
            args_append('"%s"' % arg['enum'][0])
        ]),
        opt_name_in_list,
    ],
    [
        [singlearg, optional],
        lambda arg: if_arg(arg, [args_append(name(arg))]),
        opt_name_in_list,
    ],
    [
        [singlearg],
        lambda arg: [args_append(name(arg))],
        name_in_list,
    ]
]


def get_commands(fname):
    return json.load(open(fname))


comment = lambda x: ['# %s' % i for i in x]


def main():

    fname = os.path.join(os.path.dirname(__file__), 'commands.json')
    commands = get_commands(fname)

    LINES = ['class RedisCommandsMixin(object):', '']

    for cmd, params in sorted(commands.items()):

        args = ['self']

        lines = ['    args = ["%s"]' % cmd]

        for arg in params.get('arguments', []):
            try:
                for flt, code_action, arg_action in RULES:
                    if all(i(cmd, arg) for i in flt):
                        args.extend(arg_action(arg))
                        lines.extend(indent(code_action(arg)))
                        break
                else:
                    lines.append("    # XXX: NO RULES FOR %s:%s" % (cmd, arg))
                    logging.error('FAIL %s:%s', cmd, arg, exc_info=True)
            except:
                lines.append('    # XXX: FAIL %s:%s' % (cmd, arg))
                logging.error('FAIL %s:%s', cmd, arg, exc_info=True)

        LINES.append('    def %s(%s, callback=None):' % (
            argname(cmd), ', '.join(args))
        )
        LINES.extend(indent(lines))
        LINES.extend(['        return self.send_command(args, callback)', ''])

    sys.stdout.write('\n'.join(LINES))


if __name__ == "__main__":
    main()
