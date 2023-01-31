#
# Copyright (C) 2023 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest

from charmed_openstack_info import loader
try:
    from importlib.resources import files  # type: ignore
except ImportError:
    from importlib_resources import files  # type: ignore


class TestLoader(unittest.TestCase):
    def test_find_file(self):
        expected_path = files(
            'charmed_openstack_info.data.lp-builder-config'
        ).joinpath('openstack.yaml')
        self.assertEqual(loader.find_file('openstack'),
                         expected_path)

    def test_load_file(self):
        fpath = os.path.join(os.path.dirname(__file__), 'fixtures',
                             'generic.yaml')
        charms = loader.load_file(fpath)
        self.assertEqual(len(list(charms.projects())), 1)
