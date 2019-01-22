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
    found = tg.find_tags(args.path, *args.tags, top_only=args.top, depth=args.depth)
    print('\n'.join(found))


def tagger_get(args):
    tg = FileTagger()
    tags = tg.get_tags(args.path)
    print('\n'.join(tags))


def tagger_clear(args):
    tg = FileTagger()
    res = tg.clear_tags(args.path, recursive=args.recursive, depth=args.depth, top_only=args.top)
    if not res:
        print("[-] Fail to clear tags")


def tagger_merge(args):
    tg = FileTagger()
    tg.merge_tags(args.path, args.dest_path, *args.tags)


def tagger_sync(args):
    tg = FileTagger()
    tg.sync_tags(args.path)

def get_parser():
    parser = argparse.ArgumentParser(prog="tagger")
    subparsers = parser.add_subparsers()
    # tagger add
    parser_add = subparsers.add_parser("add", help="add tags to path")
    parser_add.add_argument("path", help="path to add tags")
    parser_add.add_argument("tags", nargs="+", help="tags to add")
    parser_add.set_defaults(func=tagger_add)
    # tagger rm
    parser_rm = subparsers.add_parser("rm", help="remove tags from path")
    parser_rm.add_argument("path", help="path to remove tags from")
    parser_rm.add_argument("tags", nargs="+", help="tags to remove")
    parser_rm.set_defaults(func=tagger_rm)
    # tagger get
    parser_get = subparsers.add_parser("get", help="get tags of path")
    parser_get.add_argument("path", help="path of tags")
    parser_get.set_defaults(func=tagger_get)
    # tagger find
    parser_find = subparsers.add_parser("find", help="find paths that have tags")
    parser_find.add_argument("path", help="path to find tags")
    parser_find.add_argument("tags", nargs="+", help="tags to find")
    parser_find.add_argument("-t", "--top", help="only find top directories that have tags", action="store_true", default=False)
    parser_find.add_argument("-d", "--depth", type=int, help="depth of folder to search")
    parser_find.set_defaults(func=tagger_find)
    # tagger clear
    parser_clear = subparsers.add_parser("clear", help="clear path's tags")
    parser_clear.add_argument("path", help="path to clear tags")
    parser_clear.add_argument("-r", "--recursive", help="recursively clear tags", action="store_true", default=False)
    parser_clear.add_argument("-t", "--top", help="top only mode, valid if -r is given", action='store_true', default=False)
    parser_clear.add_argument("-d", "--depth", type=int, help="recursive depth, valid if -r is given")
    parser_clear.set_defaults(func=tagger_clear)
    # tagger merge
    parser_merge = subparsers.add_parser("merge", help="merge file with same tags to dest directory")
    parser_merge.add_argument("path", help="path to search for tags")
    parser_merge.add_argument(
        "dest_path", help="dest directory to save copy of files")
    parser_merge.add_argument("tags", nargs="+", help="tags to merge")
    parser_merge.set_defaults(func=tagger_merge)

    return parser


def main():
    try:
        parser = get_parser()
        args = parser.parse_args()
        if 'func' in args:
            args.func(args)
        else:
            parser.parse_args(['-h'])
    except KeyboardInterrupt:
        print("[-] Cancelled by user")


if __name__ == "__main__":
    main()
