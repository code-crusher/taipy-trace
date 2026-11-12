# Copyright 2021-2025 Avaiga Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import asyncio

from taipy.gui import Markdown

counter = 0


async def count_to_3(state):
    for i in range(3):
        state.counter = i + 1
        await asyncio.sleep(0.01)


md_page_async = Markdown(
    """
<|{counter}|>
"""
)
