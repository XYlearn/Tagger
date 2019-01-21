# -*-coding: utf-8

import os
import shutil
import unittest
from tagger import tagger

class TaggerTestCase(unittest.TestCase):
    def setUp(self):
        self.tagger = tagger.FileTagger()
        os.mkdir("tmp0")
        os.mkdir("tmp0/tmp1")
        os.mkdir("tmp0/tmp2")
        os.mkdir("tmp0/tmp1/tmp3")
        with open("tmp0/tmpf", "w+") as f:
            f.write("test")

    def tearDown(self):
        shutil.rmtree("tmp0")

    def test_add_tags_dir(self):
        self.assertTrue(len(self.tagger.add_tags("tmp0")) == 0)
        self.tagger.add_tags("tmp0", "test1", "test2")
        self.assertEqual(set(["test1", "test2"]),
                         set(self.tagger.get_tags("tmp0")))
        self.tagger.add_tags("tmp0", "test0")
        self.assertEqual(set(["test1", "test2", "test0"]),
                         set(self.tagger.get_tags("tmp0")))
        self.assertFalse(self.tagger.add_tags("tmp0/tmp0", "aa"))

    def test_add_tags_file(self):
        self.assertTrue(len(self.tagger.add_tags("tmp0/tmpf")) == 0)
        self.tagger.add_tags("tmp0/tmpf", "test1", "test2")
        self.assertEqual(set(["test1", "test2"]), set(
            self.tagger.get_tags("tmp0/tmpf")))
        self.tagger.add_tags("tmp0/tmpf", "test0")
        self.assertEqual(set(["test1", "test2", "test0"]),
                         set(self.tagger.get_tags("tmp0/tmpf")))

    def test_rm_tags_dir(self):
        self.tagger.add_tags("tmp0", "test1", "test2", "test3")
        res = self.tagger.rm_tags("tmp0", "test3", "test2")
        tags = self.tagger.get_tags("tmp0")
        self.assertTrue(res)
        self.assertEqual(set(["test1"]), set(tags))
        self.tagger.rm_tags("tmp0", "test1")
        self.assertEqual([], self.tagger.get_tags("tmp0"))
        self.assertFalse(self.tagger.rm_tags("tmp0/tmp0", "aa"))

    def test_rm_tags_file(self):
        self.tagger.add_tags("tmp0/tmpf", "test1", "test2", "test3")
        res = self.tagger.rm_tags("tmp0/tmpf", "test3", "test2")
        tags = self.tagger.get_tags("tmp0/tmpf")
        self.assertTrue(res)
        self.assertEqual(set(["test1"]), set(tags))
        self.tagger.rm_tags("tmp0/tmpf", "test1")
        self.assertEqual([], self.tagger.get_tags("tmp0/tmpf"))

    def test_find_tags_full_match(self):
        self.tagger.add_tags("tmp0", "test1", "test2", "test3")
        self.tagger.add_tags("tmp0/tmp1", "test1")
        self.tagger.add_tags("tmp0/tmp1/tmp3", "test1")
        self.tagger.add_tags("tmp0/tmpf", "test2")

        self.assertEqual([], self.tagger.find_tags("tmp0/tmp0", "test0"))

        paths = self.tagger.find_tags("tmp0", "test1")
        self.assertEqual(3, len(paths))
        tmp_paths = ['tmp0', 'tmp0/tmp1', 'tmp0/tmp1/tmp3']
        self.assertEqual(
            set(map(lambda path: os.path.abspath(path), tmp_paths)), set(paths))

        paths = self.tagger.find_tags("tmp0", "test2")
        self.assertEqual(2, len(paths))
        tmp_paths = ["tmp0", "tmp0/tmpf"]
        self.assertEqual(
            set(map(lambda path: os.path.abspath(path), tmp_paths)), set(paths))

        paths = self.tagger.find_tags("tmp0", "test1", "test2")
        self.assertEqual(set([os.path.abspath('tmp0')]), set(paths))

    def test_find_tags_top_only(self):
        self.tagger.add_tags("tmp0", "test2", "test3")
        self.tagger.add_tags("tmp0/tmp1", "test1")
        self.tagger.add_tags("tmp0/tmp1/tmp3", "test1")
        self.tagger.add_tags("tmp0/tmpf", "test1")

        self.assertEqual([], self.tagger.find_tags("tmp0/tmp0", "test0", top_only=True))
        paths = self.tagger.find_tags("tmp0", "test1", top_only=True)
        self.assertEqual(2, len(paths))
        self.assertEqual(set(map(lambda s: os.path.abspath(s), ['tmp0/tmpf', "tmp0/tmp1"])), set(paths))

    def test_find_tags_depth(self):
        self.tagger.add_tags("tmp0", "test2", "test3")
        self.tagger.add_tags("tmp0/tmp1", "test1")
        self.tagger.add_tags("tmp0/tmp1/tmp3", "test1")
        self.tagger.add_tags("tmp0/tmpf", "test1")

        self.assertEqual(set(map(lambda s: os.path.abspath(s), ['tmp0/tmpf', "tmp0/tmp1"])), set(self.tagger.find_tags("tmp0", "test1", depth=1)))
        self.assertEqual(set(map(lambda s: os.path.abspath(s), ['tmp0/tmpf', "tmp0/tmp1", "tmp0/tmp1/tmp3"])), set(self.tagger.find_tags("tmp0", "test1", depth=2)))

    def test_get_tags_dir(self):
        self.tagger.add_tags("tmp0", "test1", "test2", "test3")
        tags = self.tagger.get_tags("tmp0")
        self.assertTrue(len(tags) == 3)
        self.assertTrue(set(tags) == set(['test1', 'test2', 'test3']))
        self.assertEqual([], self.tagger.get_tags("tmp0/tmp1"))
        self.assertEqual([], self.tagger.get_tags("tmp0/aaa"))
        self.assertEqual([], self.tagger.get_tags("tmp0/tmp0"))

    def test_get_tags_file(self):
        self.assertEqual([], self.tagger.get_tags("tmp0/tmpf"))
        self.tagger.add_tags("tmp0/tmpf", "test1", "test2", "test3")
        tags = self.tagger.get_tags("tmp0/tmpf")
        self.assertTrue(len(tags) == 3)
        self.assertTrue(set(tags) == set(['test1', 'test2', 'test3']))

    def test_clear_tags_dir(self):
        self.tagger.add_tags("tmp0", "test1", "test2", "test3")
        self.tagger.clear_tags("tmp0")
        self.assertTrue(len(self.tagger.get_tags("tmp0")) == 0)
        self.assertFalse(self.tagger.clear_tags("tmp0/tmp0"))

    def test_clear_tags_file(self):
        self.tagger.add_tags("tmp0/tmpf", "test1", "test2", "test3")
        self.tagger.clear_tags("tmp0/tmpf")
        self.assertTrue(len(self.tagger.get_tags("tmp0")) == 0)

    def test_sync_tags(self):
        self.tagger.add_tags("tmp0/tmpf", "test0")
        os.remove("tmp0/tmpf")
        self.tagger.sync_tags("tmp0")
        with open("tmp0/tmpf", "w+") as f:
            f.write("test")
        self.assertEqual([], self.tagger.get_tags("tmp0/tmpf"))
        self.assertFalse(self.tagger.sync_tags("tmp0/tmp0"))

    def test_merge_tags(self):
        self.tagger.add_tags("tmp0", "test2", "test3")
        self.tagger.add_tags("tmp0/tmp1", "test1")
        self.tagger.add_tags("tmp0/tmp1/tmp3", "test1")
        self.tagger.add_tags("tmp0/tmpf", "test1")

        try:
            self.tagger.merge_tags("tmp0", "test2_dir", *["test2", "test3"])
            _, dirs, _ = next(os.walk('test2_dir'))
            self.assertEqual(set(['tmp0']), set(dirs))
            _, dirs, files = next(os.walk('test2_dir/tmp0'))
            self.assertEqual(set(['tmp1', 'tmp2']), set(dirs))
            self.assertTrue('tmpf' in files)
            _, dirs, _ = next(os.walk('test2_dir/tmp0/tmp1'))
            self.assertEqual(set(['tmp3']), set(dirs))
            self.assertEqual(set(['test2', 'test3']), set(self.tagger.get_tags("test2_dir")))
        finally:
            shutil.rmtree("test2_dir")

        try:
            os.mkdir("tmp0/tmp2/tmp1")
            self.tagger.add_tags("tmp0/tmp2/tmp1", "test1")
            self.tagger.merge_tags("tmp0", "test1_dir", "test1")
            _, dirs, files = next(os.walk('test1_dir'))
            self.assertEqual(set(['tmp1', "tmp1_1"]), set(dirs))
            self.assertTrue('tmpf' in files)
            self.assertEqual(set(['test1']), set(self.tagger.get_tags("test1_dir")))
        finally:
            shutil.rmtree("tmp0/tmp2/tmp1")
            shutil.rmtree("test1_dir")


if __name__ == "__main__":
    unittest.main()
