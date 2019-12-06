# Copyright (C) 2019 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import typing

from unittest.mock import MagicMock, patch

import pytest
from hamcrest import *

from autokey.configmanager.configmanager import ConfigManager
from autokey.service import PhraseRunner
import autokey.model
from autokey.scripting import Engine


def create_engine() -> typing.Tuple[Engine, autokey.model.Folder]:
    # Make sure to not write to the hard disk
    test_folder = autokey.model.Folder("Test folder")
    test_folder.persist = MagicMock()

    # Mock load_global_config to add the test folder to the known folders. This causes the ConfigManager to skip it’s
    # first-run logic.
    with patch("autokey.model.Phrase.persist"), patch("autokey.model.Folder.persist"),\
         patch("autokey.configmanager.configmanager.ConfigManager.load_global_config",
               new=(lambda self: self.folders.append(test_folder))):
        engine = Engine(ConfigManager(MagicMock()), MagicMock(spec=PhraseRunner))
        engine.configManager.config_altered(False)

    return engine, test_folder


def test_engine_create_phrase_adds_phrase_to_parent():
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"):
        phrase = engine.create_phrase(folder, "Phrase", "ABC")
    assert_that(folder.items, has_item(phrase))


def test_engine_create_phrase_duplicate_hotkey_raises_value_error():
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"):
        phrase = engine.create_phrase(folder, "Phrase", "ABC", hotkey=(["<ctrl>"], "a"))
        assert_that(folder.items, has_item(phrase))
        assert_that(
            calling(engine.create_phrase).with_args(folder, "Phrase2", "ABC", hotkey=(["<ctrl>"], "a")),
            raises(ValueError)
        )


def test_engine_create_phrase_duplicate_abbreviation_raises_value_error():
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"):
        phrase = engine.create_phrase(folder, "Phrase", "ABC", abbreviations="abbr")
        assert_that(folder.items, has_item(phrase))
        assert_that(
            calling(engine.create_phrase).with_args(folder, "Phrase", "ABC", abbreviations=["abbrev", "abbr"]),
            raises(ValueError)
        )


@pytest.mark.parametrize("invalid_abbreviations", [
    1337,
    ["abbr", 1337],
    b'bytes_are_invalid',
    [b'a', "ab"]
])
def test_engine_create_phrase_invalid_abbreviation_type(invalid_abbreviations):
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"):
        assert_that(
            calling(engine.create_phrase).with_args(folder, "Phrase", "ABC", abbreviations=invalid_abbreviations),
            raises(ValueError)
        )


def test_engine_create_phrase_set_single_abbreviation():
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"):
        phrase = engine.create_phrase(folder, "Phrase", "ABC", abbreviations="abbr")
    assert_that(phrase.abbreviations, contains("abbr"))


def test_engine_create_phrase_set_list_of_abbreviations():
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"):
        phrase = engine.create_phrase(folder, "Phrase", "ABC", abbreviations=["abbr", "Short"])
    assert_that(phrase.abbreviations, contains_inanyorder("abbr", "Short"))


def test_engine_create_phrase_set_always_prompt():
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"):
        phrase_without_prompt = engine.create_phrase(folder, "Phrase", "ABC", always_prompt=False)
        phrase_with_prompt = engine.create_phrase(folder, "Phrase2", "ABC", always_prompt=True)
    assert_that(phrase_with_prompt.prompt, is_(equal_to(True)))
    assert_that(phrase_without_prompt.prompt, is_(equal_to(False)))


def test_engine_create_phrase_set_show_in_tray():
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"):
        phrase_not_in_tray = engine.create_phrase(folder, "Phrase", "ABC", show_in_system_tray=False)
        phrase_in_tray = engine.create_phrase(folder, "Phrase2", "ABC", show_in_system_tray=True)
    assert_that(phrase_in_tray.show_in_tray_menu, is_(equal_to(True)))
    assert_that(phrase_not_in_tray.show_in_tray_menu, is_(equal_to(False)))


@pytest.mark.parametrize("send_mode", Engine.SendMode)
def test_engine_create_phrase_set_send_mode(send_mode: Engine.SendMode):
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"):
        phrase = engine.create_phrase(folder, "Phrase", "ABC", send_mode=send_mode)
    assert_that(phrase.sendMode, is_(equal_to(send_mode)))


def test_engine_create_folder():
    engine, folder = create_engine()
    # Temporary: Don't put folder on disk.
    test_folder = engine.create_folder("New folder",
            temporary=True)
    assert_that(engine.configManager.allFolders, has_item(test_folder))
