# -*-coding: utf-8-*-

import abc
import os
import re
import logging
import json
import time
import shutil
from collections import deque

logger = logging.getLogger(__name__)


class Tagger(abc.ABC):
    def add_tags(self, path, *tags, **kwargs):
        '''add tags to path
        Args:
            path(str): path of tags
            *tags(str): tags to add
        Return(boolean): whether tags are added successfully. if path doesn't exist reuturn false
        '''
        if not tags or not os.path.exists(path):
            return []
        old_tags = self.get_tags(path)
        new_tags = list(set(old_tags + list(tags)))
        res = self._write_tags(path, new_tags)
        return res

    def rm_tags(self, path, *tags, **kwargs):
        '''remove tags from path
        Args:
            path(str): path to delete tags from
            *tags(str): tags to delete
        Return(boolean): whether tags are removed successfully. if path doesn't exist reuturn false
        '''
        if not os.path.exists(path):
            return False
        old_tags = set(self.get_tags(path))
        new_tags = old_tags.difference(set(tags))
        res = self._write_tags(path, new_tags)
        return res

    def find_tags(self, path, *tags, **kwargs):
        '''find tags in path
        Args:
            path(str): dir path to recursively search for tags; or file path to search only for that file.
            *tags(str): tags to search. at least one tag is given
            **kwargs:
                top_only(boolean): only top directories or files will be returned
        Return(list(str)): abs paths that hold tags. if path doesn't exist reuturn empty list
        '''
        if not os.path.exists(path):
            return []
        if not os.path.isdir(path):
            file_tags = set(self.get_tags(path))
            if file_tags.issuperset(set(tags)):
                return [os.path.abspath(path)]
            else:
                return []
        if kwargs.get("top_only"):
            return self._find_tags_top_only(path, *tags, **kwargs)
        else:
            return self._find_tags_all(path, *tags, **kwargs)

    def get_tags(self, path, **kwargs):
        '''get tags in path
        Args:
            path(str): path to get tags from
        Return(list(str)): tags of that path. if path doesn't exist reuturn empty list
        '''
        if not os.path.exists(path):
            return []
        tags = self._read_tags(path)
        tags.sort()
        return tags

    def clear_tags(self, path, **kwargs):
        '''clear tags in path
        Args:
            path(str): path to clear tags from
            **kwargs:
                recursive(boolean): whether to clear tags recursively
                depth(int): depth to recursively remove tags. valid only if recursive is True
                top_only: only clear tags of top folder or files. valid only if recursive is True
        Return(boolean): If path doesn't exist reuturn false
        '''
        if not os.path.exists(path):
            return False
        if not os.path.isdir(path):
            return self._write_tags(path, [])
        if not kwargs.get('recursive'):
            return self._write_tags(path, [])
        depth = kwargs.get('depth')
        path_gen = self._possible_tagged_paths(path, depth=depth)
        top_only = kwargs.get('top_only')
        try:
            ret = path_gen.send(None)
            while True:
                p, is_dir = ret
                self._write_tags(p, [])
                if is_dir:
                    # stop if in top only mode
                    ret = path_gen.send(top_only)
                    continue
                ret = path_gen.send(False)
        except StopIteration:
            pass
        return True

    @abc.abstractmethod
    def sync_tags(self, path, **kwargs):
        '''synchronize tags with file in path. non-existent entry will me removed
        Args:
            path(str): path to synchronze
        Return(boolean): True if succeed. if path doesn't exist reuturn false
        '''
        pass

    def merge_tags(self, path, dest_path, *tags, **kwargs):
        '''copy all top directories or files that have tags to dest_path.
        and add tags to dest_path. duplicated path name will be renamed to
        $name_1, $name_2, etc.
        Args:
            path(str): path to search for tags
            dest_path(str): path to store found files
            *tags(str): tags to search for
        Return(boolean): return True if succeed.
        '''
        # merge single file is meaningless
        if not os.path.isdir(path):
            return False
        # check dest_path
        if os.path.exists(dest_path):
            if not os.path.isdir(dest_path):
                return False
        else:
            try:
                os.mkdir(dest_path)
            except:
                return False
        paths = self.find_tags(path, *tags, top_only=True, **kwargs)
        for p in paths:
            target = os.path.join(dest_path, os.path.basename(p))
            target = self._handle_dup_path(p, target)
            try:
                if os.path.isdir(p):
                    shutil.copytree(p, target)
                else:
                    shutil.copy2(p, target)
                    self.add_tags(target, *self.get_tags(p))
            except:
                logger.warn("[!] Fail to copy {} to {}".format(p, target))
        self.add_tags(dest_path, *tags)

    @abc.abstractmethod
    def _read_tags(self, path):
        '''read tags of path. path must exist'''
        pass

    @abc.abstractmethod
    def _write_tags(self, path, tags):
        '''write tags of path. path must exist.'''
        pass

    def _possible_tagged_paths(self, root, depth=None):
        '''get abs paths that possible have tag under root(including root). root must be existent directory.
        The yield paths' order is top folder => common files in top folder => recursively to sub folders and its files
        Args:
            root: root path
            depth: depth of path to find
        Return(corouting): every time return a possible path, formatted as tuple(path, is_dir) then receive 
            a boolean value specific whether to continue under that path.
        '''
        curr_depth = 0
        roots = deque([root])
        tmp_roots = deque()
        while len(roots):
            sub_roots = deque()
            while len(roots):
                top = roots.pop()
                if self._possible_has_tag_entry(top):
                    stop = yield top, True
                    if not stop:
                        tmp_roots.appendleft(top)
                else:
                    # only search sub dirs
                    scandir_it = os.scandir(top)
                    sub_roots.extendleft(map(lambda entry: entry.path, filter(
                        lambda entry: entry.is_dir(), scandir_it)))
            if curr_depth == depth:
                break
            roots = sub_roots
            while len(tmp_roots):
                top = tmp_roots.pop()
                scandir_it = os.scandir(top)
                for entry in scandir_it:
                    if entry.is_dir():
                        roots.appendleft(entry.path)
                    else:
                        _ = yield entry.path, False
            curr_depth += 1

    def _possible_has_tag_entry(self, directory, recursive=False):
        '''whether directory or file under directory possible has tag. this is for speed improvement
        directory must exist
        '''
        return True

    def _find_tags_top_only(self, path, *tags, **kwargs):
        '''path must exist'''
        paths = []
        path_gen = self._possible_tagged_paths(path, depth=kwargs.get('depth'))
        try:
            ret = path_gen.send(None)
            while True:
                p, is_dir = ret
                if self._contain_tags(p, *tags):
                    paths.append(os.path.abspath(p))
                    if is_dir:
                        ret = path_gen.send(True)
                        continue
                ret = path_gen.send(False)
        except StopIteration:
            pass
        return paths

    def _find_tags_all(self, path, *tags, **kwargs):
        paths = []
        path_gen = self._possible_tagged_paths(path, depth=kwargs.get('depth'))
        try:
            ret = path_gen.send(None)
            while True:
                p, _ = ret
                if self._contain_tags(p, *tags):
                    paths.append(os.path.abspath(p))
                ret = path_gen.send(False)
        except StopIteration:
            pass
        return paths

    def _contain_tags(self, path, *tags):
        return set(tags).issubset(set(self.get_tags(path)))

    def _handle_dup_path(self, path, target):
        '''handle dup path when merging
        Args:
            path(str): origin path of file
            target(str): target path that might be duplicated
        Return(str): name not duplicated.
        '''
        if os.path.exists(target):
            postfix = 1
            while os.path.exists("{}_{}".format(target, postfix)):
                postfix += 1
            target = "{}_{}".format(target, postfix)
            logger.info("[*] {} duplicate, rename to {}".format(path, target))
        return target


class FileTagger(Tagger):
    TAG_FILE = '.tag'

    def sync_tags(self, path):
        if not os.path.exists(path):
            return False
        meta = self.__read_tag_meta(path)
        dangler_paths = []
        for _path in meta:
            if not os.path.exists(_path):
                dangler_paths.append(_path)
        for _path in dangler_paths:
            meta.pop(_path)
        self.__write_tag_meta(path, meta)

    def _read_tags(self, path):
        _path = os.path.abspath(path)
        meta = self.__read_tag_meta(_path)
        tags = meta.get(_path)
        if tags:
            return tags
        else:
            return []

    def _write_tags(self, path, tags):
        _path = os.path.abspath(path)
        meta = self.__read_tag_meta(_path)
        if not tags:
            if _path in meta:
                meta.pop(_path)
        else:
            meta[_path] = list(set(tags))
        return self.__write_tag_meta(path, meta)

    def _possible_has_tag_entry(self, directory, recursive=False):
        return os.path.exists(self.__get_tag_file(os.path.abspath(directory)))

    def __read_tag_meta(self, path):
        tag_file = self.__get_tag_file(path)
        if not tag_file:
            return {}
        try:
            with open(tag_file, "r", encoding='utf-8') as f:
                meta = json.load(f)
            return meta
        except:
            return {}

    def __write_tag_meta(self, path, meta):
        tag_file = self.__get_tag_file(path)
        if not meta:
            if not os.path.exists(tag_file):
                return True
            try:
                os.remove(tag_file)
                return True
            except:
                return False
        else:
            try:
                with open(tag_file, "w+", encoding='utf-8') as f:
                    json.dump(meta, f)
                return True
            except:
                return False

    def __get_tag_file(self, abspath):
        if os.path.isfile(abspath):
            abspath = os.path.dirname(abspath)
        tag_file = os.path.join(abspath, self.TAG_FILE)
        return tag_file


class DBTagger(Tagger):
    def __init__(self):
        pass

    def _load_db(self, db_path):
        pass

    def _save_db(self, db_path):
        pass
