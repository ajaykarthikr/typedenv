import importlib
import os
import tempfile
import unittest
from unittest.mock import patch

import newenvreader


class TestFindAndReadEnv(unittest.TestCase):
    def setUp(self):
        os.environ["MY_VAR"] = "12121"
        self.env_data = "VAR1=value1\nVAR2=value2\nVAR3=12121\n"

        self.temp_dir = tempfile.TemporaryDirectory()

    def test_read_env(self):
        file_path = os.path.join(self.temp_dir.name, ".env")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.env_data)

        with patch("os.getcwd", return_value=self.temp_dir.name):
            importlib.reload(newenvreader)

            val = newenvreader.get_env("MY_VAR", cast=int)
            assert val == 12121

            val = newenvreader.get_env("VAR1")
            assert val == "value1"

            val = newenvreader.get_env("VAR1")
            assert val == "value1"

        # Delete the temp file
        os.remove(file_path)

    def test_root_env_file(self):
        subdir_path = os.path.join(self.temp_dir.name, "subdir")
        os.mkdir(subdir_path)

        file_path = os.path.join(subdir_path, ".env")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.env_data)

        with patch("os.getcwd", return_value=subdir_path):
            importlib.reload(newenvreader)

            val = newenvreader.get_env("MY_VAR", cast=float)
            assert val == 12121

            val = newenvreader.get_env("VAR1")
            assert val == "value1"

            val = newenvreader.get_env("VAR3", cast=int)
            assert val == 12121

        # Delete the temp file
        os.remove(file_path)

    def test_parse_env_file_empty(self):
        file_path = os.path.join(self.temp_dir.name, ".env")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.env_data)

        with patch("os.getcwd", return_value=self.temp_dir.name):
            importlib.reload(newenvreader)

        val = newenvreader.get_env("MY_VAR", cast=int)
        assert val == 12121

        os.remove(file_path)

    def test_ini_file(self):
        file_data = """
        [settings]
        VAR1=12
        VAR2=Value2
        """
        file_path = os.path.join(self.temp_dir.name, "settings.ini")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(file_data)

        with patch("os.getcwd", return_value=self.temp_dir.name):
            importlib.reload(newenvreader)

        # assert newenvreader.get_env("VAR1", cast=int) == 12

        os.remove(file_path)

    def test_invalid_ini_file(self):
        # Reload at start to clear any previous settings which don't get cleared
        # when the module is reloaded as an exception is raised due to 
        # invalid ini file
        with patch("os.getcwd", return_value=self.temp_dir.name):
            importlib.reload(newenvreader)
        
        file_data = """
        VAR1=12121
        VAR2=Value2
        """
        file_path = os.path.join(self.temp_dir.name, "settings.ini")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(file_data)

        with patch("os.getcwd", return_value=self.temp_dir.name):
            with self.assertRaises(ValueError):
                importlib.reload(newenvreader)
    
        os.remove(file_path)

    def tearDown(self):
        del os.environ["MY_VAR"]
        self.temp_dir.cleanup()


class TestEnvParsing(unittest.TestCase):
    def setUp(self):
        os.environ["MY_VAR"] = "12121"
        os.environ["KEY_NOT_OVERRIDDEN_BY_ENV"] = "Normal"

        env_data = """STR_VAL=value1
        StrVal=value2
        INT_VAL=12121
        FLOAT_VAL=32.1234
        COMPL_VAL=postgresql://user:pass@localhost:5432/db

        BOOL_VAL_TRUE=True
        BOOL_VAL_FALSE=False
        BOOL_VAL_NUM1=1
        BOOL_VAL_NUM0=0
        BOOL_VAL_true=true
        BOOL_VAL_false=false
        BOOL_VAL_True=True
        BOOL_VAL_False=False

        EMPTY_VAL=
        VAL_WITH_SPACE=Line 1

        #CommentedKey=None
        #COMMENTED_KEY=None
        PERCENT_NOT_ESCAPED=%%
        NO_INTERPOLATION=%(KeyOff)s
        IGNORE_SPACE = text
        RESPECT_SINGLE_QUOTE_SPACE = ' text'
        RESPECT_DOUBLE_QUOTE_SPACE = " text"
        KEY_NOT_OVERRIDDEN_BY_ENV=Overide

        VAL_WITH_SINGLE_QUOTE_END=text'
        VAL_WITH_SINGLE_QUOTE_MID=te'xt
        VAL_WITH_SINGLE_QUOTE_BEGIN='text
        VAL_WITH_DOUBLE_QUOTE_END=text"
        VAL_WITH_DOUBLE_QUOTE_MID=te"xt
        VAL_WITH_DOUBLE_QUOTE_BEGIN="text
        VAL_IS_SINGLE_QUOTE='
        VAL_IS_DOUBLE_QUOTE="
        VAL_HAS_TWO_SINGLE_QUOTE="'Y'"
        VAL_HAS_TWO_DOUBLE_QUOTE='"Y"'
        VAL_HAS_MIXED_QUOTES_AS_DATA1="Y'
        VAL_HAS_MIXED_QUOTES_AS_DATA2='Y"
        """

        self.temp_dir = tempfile.TemporaryDirectory()
        file_path = os.path.join(self.temp_dir.name, ".env")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(env_data)

        with patch("os.getcwd", return_value=self.temp_dir.name):
            importlib.reload(newenvreader)
        self.file_path = file_path

    def test_env_normal(self):
        assert newenvreader.get_env("MY_VAR", cast=int) == 12121
        assert newenvreader.get_env("STR_VAL") == "value1"
        assert newenvreader.get_env("StrVal") == "value2"
        assert newenvreader.get_env("INT_VAL") == "12121"
        assert (
            newenvreader.get_env("COMPL_VAL")
            == "postgresql://user:pass@localhost:5432/db"
        )

    def test_env_bool_casting(self):
        assert newenvreader.get_env("BOOL_VAL_TRUE", cast=bool) is True
        assert newenvreader.get_env("BOOL_VAL_FALSE", cast=bool) is False
        assert newenvreader.get_env("BOOL_VAL_NUM1", cast=bool) is True
        assert newenvreader.get_env("BOOL_VAL_NUM0", cast=bool) is False
        assert newenvreader.get_env("BOOL_VAL_true", cast=bool) is True
        assert newenvreader.get_env("BOOL_VAL_false", cast=bool) is False
        assert newenvreader.get_env("BOOL_VAL_True", cast=bool) is True
        assert newenvreader.get_env("BOOL_VAL_False", cast=bool) is False

        # Test default casting
        assert newenvreader.get_env("TEST_VAR", default=1, cast=bool) is True
        assert newenvreader.get_env("TEST_VAR", default=0, cast=bool) is False
        assert newenvreader.get_env("TEST_VAR", default=2, cast=bool) is True

        # Invalid values
        with self.assertRaises(ValueError):
            newenvreader.get_env("STR_VAL", cast=bool)

    def test_env_int_casting(self):
        assert newenvreader.get_env("INT_VAL", cast=int) == 12121
        assert newenvreader.get_env("VAR11", default=12, cast=int) == 12
        # Check for exception
        with self.assertRaises(ValueError):
            newenvreader.get_env("STR_VAL", cast=int)

    def test_env_val_edges(self):
        with self.assertRaises(KeyError):
            newenvreader.get_env("COMMENTED_KEY")

        assert newenvreader.get_env("PERCENT_NOT_ESCAPED") == "%%"
        assert newenvreader.get_env("NO_INTERPOLATION") == "%(KeyOff)s"
        assert newenvreader.get_env("IGNORE_SPACE") == "text"
        assert newenvreader.get_env("RESPECT_SINGLE_QUOTE_SPACE") == " text"
        assert newenvreader.get_env("RESPECT_DOUBLE_QUOTE_SPACE") == " text"
        assert newenvreader.get_env("KEY_NOT_OVERRIDDEN_BY_ENV") == "Overide"

        

    def test_env_val_quotes(self):
        assert newenvreader.get_env("VAL_WITH_SINGLE_QUOTE_END") == "text'"
        assert newenvreader.get_env("VAL_WITH_SINGLE_QUOTE_MID") == "te'xt"
        assert newenvreader.get_env("VAL_WITH_SINGLE_QUOTE_BEGIN") == "'text"
        assert newenvreader.get_env("VAL_WITH_DOUBLE_QUOTE_END") == 'text"'
        assert newenvreader.get_env("VAL_WITH_DOUBLE_QUOTE_MID") == 'te"xt'
        assert newenvreader.get_env("VAL_WITH_DOUBLE_QUOTE_BEGIN") == '"text'
        assert newenvreader.get_env("VAL_IS_SINGLE_QUOTE") == "'"
        assert newenvreader.get_env("VAL_IS_DOUBLE_QUOTE") == '"'
        assert newenvreader.get_env("VAL_HAS_TWO_SINGLE_QUOTE") == "'Y'"
        assert newenvreader.get_env("VAL_HAS_TWO_DOUBLE_QUOTE") == '"Y"'
        assert newenvreader.get_env("VAL_HAS_MIXED_QUOTES_AS_DATA1") == """"Y\'"""
        assert newenvreader.get_env("VAL_HAS_MIXED_QUOTES_AS_DATA2") == '''\'Y"'''

    def tearDown(self):
        del os.environ["MY_VAR"]
        del os.environ["KEY_NOT_OVERRIDDEN_BY_ENV"]
        os.remove(self.file_path)
        self.temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
