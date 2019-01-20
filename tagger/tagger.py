# -*-coding: utf-8-*-

import abc
import os
import re
import logging
import json
import time


class Tagger(abc.ABC):
    def add_tags(self, path, *tags, **kwargs):
        '''add tags to path
        Args:
            path(str): path of tags
            *tags(list(str)): tags to add
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
            *tags(list(str)): tags to delete
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
            *tags(list(str)): tags to search
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
        paths = []
        for root, _, files in os.walk(path):
            target_paths = [os.path.join(root, f) for f in files]
            target_paths.append(root)
            for target in target_paths:
                if set(tags).issubset(set(self.get_tags(target))):
                    paths.append(os.path.abspath(target))
        return paths

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

    @abc.abstractmethod
    def _read_tags(self, path):
        '''read tags of path. path must exist'''
        pass

    @abc.abstractmethod
    def _write_tags(self, path, tags):
        '''write tags of path. path must exist'''
        pass


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
