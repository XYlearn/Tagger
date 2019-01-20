# -*-coding: utf-8

import sys
import argparse
from tagger import FileTagger


def tagger_add(args):
    tg = FileTagger()
    res = tg.add_tags(args.path, *args.tags)
    if not res:
        print("[-] Fail to add tags.")


def tagger_rm(args):
    tg = FileTagger()
    res = tg.rm_tags(args.path, *args.tags)
    if not res:
        print("[-] Fail to remove tags.")


def tagger_find(args):
    tg = FileTagger()
    found = tg.find_tags(args.path, *args.tags)
    print('\n'.join(found))


def tagger_get(args):
    tg = FileTagger()
    tags = tg.get_tags(args.path)
    print('\n'.join(tags))


def tagger_clear(args):
    tg = FileTagger()
    res = tg.clear_tags(args.path)
    if not res:
        print("[-] Fail to clear tags")


def get_parser():
    parser = argparse.ArgumentParser(prog="tagger")
    subparsers = parser.add_subparsers()
    # tagger add
    parser_add = subparsers.add_parser(
        "add", help="tagger add [path] [tags..]")
    parser_add.add_argument("path", help="path to add tags")
    parser_add.add_argument("tags", nargs="*", help="tags to add")
    parser_add.set_defaults(func=tagger_add)
    # tagger rm
    parser_rm = subparsers.add_parser("rm", help="tagger rm [path] [tags..]")
    parser_rm.add_argument("path", help="path to remove tags from")
    parser_rm.add_argument("tags", nargs="*", help="tags to remove")
    parser_rm.set_defaults(func=tagger_rm)
    # tagger get
    parser_get = subparsers.add_parser("get", help="tagger get [path]")
    parser_get.add_argument("path", help="path of tags")
    parser_get.set_defaults(func=tagger_get)
    # tagger find
    parser_find = subparsers.add_parser("find", help="find tags path")
    parser_find.add_argument("path", help="path to find tags")
    parser_find.add_argument("tags", nargs="*", help="tags to find")
    parser_find.set_defaults(func=tagger_find)
    # tagger clear
    parser_clear = subparsers.add_parser("clear", help="tagger clear [path]")
    parser_clear.add_argument("path", help="path to clear tags")
    parser_clear.set_defaults(func=tagger_clear)

    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.parse_args(['-h'])


if __name__ == "__main__":
    main()    