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
            *tags(str): tags to search
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
            return self.__find_tags_top_only(path, *tags)
        else:
            return self.__find_tags_all(path, *tags)

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
        Return(boolean): True if succeed. if path doesn't exist reuturn false
        '''
        if not os.path.exists(path):
            return False
        return self._write_tags(path, [])

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
        paths = self.find_tags(path, *tags, top_only=True)
        for p in paths:
            target = os.path.join(dest_path, os.path.basename(p))
            target = self.__handle_dup_path(p, target)
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

    def __find_tags_top_only(self, path, *tags):
        '''path must exist'''
        # use BFS
        roots = deque([path])
        paths = []
        while len(roots):
            _path = roots.pop()
            root, dirs, files = next(os.walk(_path))
            if self.__contain_tags(root, *tags):
                paths.append(os.path.abspath(root))
            for f in map(lambda f: os.path.join(root, f), files):
                if self.__contain_tags(f, *tags):
                    paths.append(os.path.abspath(f))
            for d in map(lambda d: os.path.join(root, d), dirs):
                if self.__contain_tags(d, *tags):
                    paths.append(os.path.abspath(d))
                else:
                    roots.append(d)
        return paths

    def __find_tags_all(self, path, *tags):
        paths = []
        for root, _, files in os.walk(path):
            target_paths = [os.path.join(root, f) for f in files]
            target_paths.append(root)
            for target in target_paths:
                if self.__contain_tags(target, *tags):
                    paths.append(os.path.abspath(target))
        return paths

    def __contain_tags(self, path, *tags):
        return set(tags).issubset(set(self.get_tags(path)))

    def __handle_dup_path(self, path, target):
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

    def __get_tag_file(self, path):
        _path = os.path.abspath(path)
        if os.path.isfile(path):
            _path = os.path.dirname(_path)
        tag_file = os.path.join(_path, self.TAG_FILE)
        return tag_file


class DBTagger(Tagger):
    def __init__(self):
        pass

    def _load_db(self, db_path):
        pass

    def _save_db(self, db_path):
        pass
