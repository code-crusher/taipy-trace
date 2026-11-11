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
from unittest.mock import Mock, patch

from taipy import Gui
from taipy.core.notification import Event, EventEntityType, EventOperation
from taipy.core.submission.submission_status import SubmissionStatus
from taipy.gui_core._context import _GuiCoreContext
from taipy.gui_core._utils import _ClientStatus

SUBMISSION_ID = "SUBMISSION_id"
SCENARIO_ID = "SCENARIO_id"
CLIENT_ID = "client_id"


def _make_submission(status=SubmissionStatus.RUNNING, client_id=CLIENT_ID):
    submission = Mock()
    submission.id = SUBMISSION_ID
    submission.entity_id = SCENARIO_ID
    submission.entity_type = "Scenario"
    submission.submission_status = status
    submission.jobs = []
    submission.properties = {"client_id": client_id} if client_id else {}
    return submission


def _make_submission_event():
    return Event(entity_type=EventEntityType.SUBMISSION, operation=EventOperation.UPDATE, entity_id=SUBMISSION_ID)


class TestGuiCoreContextProcessSubmissionEvent:
    def test_submission_from_user_callback_broadcasts_jobs(self):
        """A submission not initiated by a GUI control must still refresh the job selector (issue #2869)."""
        submission = _make_submission()
        with (
            patch("taipy.gui_core._context.core_get", return_value=submission),
            patch("taipy.gui.gui.Gui._broadcast") as mock_broadcast,
            patch("taipy.gui.gui.Gui._get_authorization"),
            patch("taipy.gui.gui.Gui.invoke_callback") as mock_invoke,
        ):
            gui_core_context = _GuiCoreContext(Gui())
            assert not gui_core_context.client_submission

            gui_core_context.process_event(event=_make_submission_event())

            mock_invoke.assert_not_called()
            mock_broadcast.assert_called_once_with(
                "core_changed",
                {
                    "tasks": {},
                    "jobs": True,
                    "scenario": SCENARIO_ID,
                    "submission": SubmissionStatus.RUNNING.value,
                },
                CLIENT_ID,
            )

    def test_submission_from_user_callback_without_client_id_broadcasts_jobs(self):
        submission = _make_submission(client_id=None)
        with (
            patch("taipy.gui_core._context.core_get", return_value=submission),
            patch("taipy.gui.gui.Gui._broadcast") as mock_broadcast,
            patch("taipy.gui.gui.Gui._get_authorization") as mock_get_auth,
        ):
            gui_core_context = _GuiCoreContext(Gui())
            gui_core_context.process_event(event=_make_submission_event())

            mock_get_auth.assert_called_once_with(system=True)
            mock_broadcast.assert_called_once_with(
                "core_changed",
                {
                    "jobs": True,
                    "scenario": SCENARIO_ID,
                    "submission": SubmissionStatus.RUNNING.value,
                },
                None,
            )

    def test_submission_from_gui_control_invokes_callback_and_broadcasts_jobs(self):
        submission = _make_submission(status=SubmissionStatus.RUNNING)
        submission.properties["on_submission"] = "on_submission"
        submission.properties["module_context"] = "module"
        with (
            patch("taipy.gui_core._context.core_get", return_value=submission),
            patch("taipy.gui.gui.Gui._broadcast") as mock_broadcast,
            patch("taipy.gui.gui.Gui._get_authorization"),
            patch("taipy.gui.gui.Gui.invoke_callback") as mock_invoke,
        ):
            gui_core_context = _GuiCoreContext(Gui())
            gui_core_context.client_submission[SUBMISSION_ID] = _ClientStatus(CLIENT_ID, SubmissionStatus.PENDING)

            gui_core_context.process_event(event=_make_submission_event())

            mock_invoke.assert_called_once()
            mock_broadcast.assert_called_once_with(
                "core_changed",
                {
                    "tasks": {},
                    "jobs": True,
                    "scenario": SCENARIO_ID,
                    "submission": SubmissionStatus.RUNNING.value,
                },
                CLIENT_ID,
            )

    def test_submission_from_gui_control_with_same_status_does_not_invoke_callback(self):
        submission = _make_submission(status=SubmissionStatus.RUNNING)
        submission.properties["on_submission"] = "on_submission"
        with (
            patch("taipy.gui_core._context.core_get", return_value=submission),
            patch("taipy.gui.gui.Gui._broadcast") as mock_broadcast,
            patch("taipy.gui.gui.Gui._get_authorization"),
            patch("taipy.gui.gui.Gui.invoke_callback") as mock_invoke,
        ):
            gui_core_context = _GuiCoreContext(Gui())
            gui_core_context.client_submission[SUBMISSION_ID] = _ClientStatus(CLIENT_ID, SubmissionStatus.RUNNING)

            gui_core_context.process_event(event=_make_submission_event())

            mock_invoke.assert_not_called()
            mock_broadcast.assert_called_once()
            assert SUBMISSION_ID in gui_core_context.client_submission

    def test_finished_submission_is_unregistered(self):
        submission = _make_submission(status=SubmissionStatus.COMPLETED)
        with (
            patch("taipy.gui_core._context.core_get", return_value=submission),
            patch("taipy.gui.gui.Gui._broadcast"),
            patch("taipy.gui.gui.Gui._get_authorization"),
            patch("taipy.gui.gui.Gui.invoke_callback"),
        ):
            gui_core_context = _GuiCoreContext(Gui())
            gui_core_context.client_submission[SUBMISSION_ID] = _ClientStatus(CLIENT_ID, SubmissionStatus.RUNNING)

            gui_core_context.process_event(event=_make_submission_event())

            assert SUBMISSION_ID not in gui_core_context.client_submission
