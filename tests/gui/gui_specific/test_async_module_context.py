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

import contextlib
import inspect
import time
import warnings

from taipy.gui import Gui

from .state_asset.page_async import count_to_3, md_page_async

PAGE_MODULE = "tests.gui.gui_specific.state_asset.page_async"


@contextlib.contextmanager
def get_state(gui: Gui, state_id: str):
    with gui.get_app_context():
        client_id = gui._bindings()._get_or_create_scope(state_id)[0]
        gui._Gui__set_client_id_in_context(client_id)  # type: ignore[attr-defined]
        yield gui._Gui__state  # type: ignore[attr-defined]


def _wait_for_counter(gui: Gui, state_id: str, expected: int):
    for _ in range(100):
        with get_state(gui, state_id) as state:
            if state["page_async"].counter == expected:
                return
        time.sleep(0.01)


def test_async_callback_module_context(gui: Gui, helpers):
    gui._set_frame(inspect.currentframe())
    gui.add_page("page_async", md_page_async)
    gui.run(run_server=False)
    server_test_client = gui._server.test_client()
    cid = helpers.create_scope_and_get_sid(gui)
    # Get the jsx once so that the page will be evaluated -> variable will be registered
    server_test_client.get(f"/{Gui._JSX_URL}/page_async?client_id={cid}")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with get_state(gui, cid):
            with gui._set_locals_context(PAGE_MODULE):
                gui._call_function_with_state(count_to_3, [])
        _wait_for_counter(gui, cid, 3)
        with get_state(gui, cid) as state:
            assert state["page_async"].counter == 3
    assert len(w) == 0, [str(wm.message) for wm in w]


def test_async_callback_page_context(gui: Gui, helpers):
    """The page context can also be selected explicitly with state["page_name"]."""
    gui._set_frame(inspect.currentframe())
    gui.add_page("page_async", md_page_async)
    gui.run(run_server=False)
    server_test_client = gui._server.test_client()
    cid = helpers.create_scope_and_get_sid(gui)
    server_test_client.get(f"/{Gui._JSX_URL}/page_async?client_id={cid}")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with get_state(gui, cid) as state:
            with gui._set_locals_context(PAGE_MODULE):
                gui._call_function_with_state(count_to_3, [state["page_async"]])
        _wait_for_counter(gui, cid, 3)
        with get_state(gui, cid) as state:
            assert state["page_async"].counter == 3
    assert len(w) == 0, [str(wm.message) for wm in w]
