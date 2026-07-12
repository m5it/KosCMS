#!/usr/bin/env python3
"""Unit tests for workflow models."""

from webcms.workflow.models import WorkflowState, WorkflowTransition, WorkflowDefinition


def test_workflow_state_to_dict():
    state = WorkflowState("draft", "Draft", "Draft content", is_initial=True)
    data = state.to_dict()
    assert data["state_id"] == "draft"
    assert data["is_initial"] is True


def test_workflow_definition_get_initial():
    states = [
        WorkflowState("draft", "Draft", "Draft", is_initial=True),
        WorkflowState("published", "Published", "Published", is_final=True)
    ]
    wf = WorkflowDefinition("wf-1", "Editorial", states=states, transitions=[])
    initial = wf.get_initial_state()
    assert initial.state_id == "draft"


def test_workflow_definition_get_transition():
    transitions = [WorkflowTransition("t1", "draft", "review", "Submit")]
    wf = WorkflowDefinition("wf-1", "Editorial", transitions=transitions)
    t = wf.get_transition("draft", "review")
    assert t is not None
    assert t.transition_id == "t1"
