import pytest

from unittest.mock import Mock

from langchain.schema.messages import (
    AIMessage,
    AIMessageChunk,
)
from ..base import (
    fake_llm_responses,
    make_api_request,
    # TEST_BASIC_MESSAGES,
    # TEST_TOOL_CALL_RESPONSE_MESSAGES,
)


def test_missing_preset(test_config, tool_manager, provider_manager, preset_manager):
    request_overrides = {
        "preset": "missing_preset",
    }
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        request_overrides=request_overrides,
    )
    success, response, user_message = request.set_request_llm()
    assert success is False
    assert "Preset 'missing_preset' not found" in user_message


def test_successful_message_string_non_streaming_request(
    test_config, tool_manager, provider_manager, preset_manager
):
    request = make_api_request(test_config, tool_manager, provider_manager, preset_manager)
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, _user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert success is True
    assert response == "test response"
    assert len(new_messages) == 3
    assert new_messages[0]["role"] == "system"
    assert new_messages[1]["role"] == "user"
    assert new_messages[2]["role"] == "assistant"


def test_successful_messages_list_non_streaming_request(
    test_config, tool_manager, provider_manager, preset_manager
):
    system_message_content = 'test system message'
    user_message_content = 'test user message'
    assistant_message_content = 'test assistant response'
    user_message_content_2 = 'test user message 2'
    messages = [
        {'role': 'system', 'content': system_message_content},
        {'role': 'user', 'content': user_message_content},
        {'role': 'assistant', 'content': assistant_message_content},
        {'role': 'user', 'content': user_message_content_2},
    ]
    request = make_api_request(test_config, tool_manager, provider_manager, preset_manager, input=messages)
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, _user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert success is True
    assert response == "test response"
    assert len(new_messages) == 5
    assert new_messages[0]["role"] == "system"
    assert new_messages[1]["role"] == "user"
    assert new_messages[2]["role"] == "assistant"
    assert new_messages[3]["role"] == "user"
    assert new_messages[4]["role"] == "assistant"


def test_execute_llm_non_streaming_failure_call_llm(
    test_config, tool_manager, provider_manager, preset_manager
):
    request = make_api_request(test_config, tool_manager, provider_manager, preset_manager)
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    request.llm = Mock()
    request.llm.invoke = Mock(side_effect=ValueError("Error"))
    success, response_obj, user_message = request.call_llm(messages)
    assert success is False
    assert str(user_message) == "Error"


def test_execute_message_string_llm_streaming(test_config, tool_manager, provider_manager, preset_manager):
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        request_overrides={"stream": True},
    )
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, _user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert success is True
    assert response == "test response"
    assert len(new_messages) == 3
    assert new_messages[0]["role"] == "system"
    assert new_messages[1]["role"] == "user"
    assert new_messages[2]["role"] == "assistant"


def test_execute_messages_list_llm_streaming(test_config, tool_manager, provider_manager, preset_manager):
    system_message_content = 'test system message'
    user_message_content = 'test user message'
    assistant_message_content = 'test assistant response'
    user_message_content_2 = 'test user message 2'
    messages = [
        {'role': 'system', 'content': system_message_content},
        {'role': 'user', 'content': user_message_content},
        {'role': 'assistant', 'content': assistant_message_content},
        {'role': 'user', 'content': user_message_content_2},
    ]
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        input=messages,
        request_overrides={"stream": True},
    )
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, _user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert success is True
    assert response == "test response"
    assert len(new_messages) == 5
    assert new_messages[0]["role"] == "system"
    assert new_messages[1]["role"] == "user"
    assert new_messages[2]["role"] == "assistant"
    assert new_messages[3]["role"] == "user"
    assert new_messages[4]["role"] == "assistant"


def test_execute_llm_streaming_failure_call_llm(
    test_config, tool_manager, provider_manager, preset_manager
):
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        request_overrides={"stream": True},
    )
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    request.llm = Mock()
    request.llm.stream = Mock(side_effect=ValueError("Error"))
    success, response_obj, user_message = request.call_llm(messages)
    assert success is False
    assert str(user_message) == "Error"


def test_post_response_full_tool_run(
    test_config, tool_manager, provider_manager, preset_manager
):
    preset = preset_manager.presets["test"]
    tool_responses = [
        AIMessage(
            content="",
            additional_kwargs={
                "tool_call": {
                    "name": "test_tool",
                    "arguments": '{\n  "word": "foo",\n  "repeats": 2\n}',
                }
            },
        ),
        "Foo repeated twice is: foo foo",
    ]
    request_overrides = {
        "preset_overrides": {
            "model_customizations": {
                "model_kwargs": {
                    "tools": [
                        "test_tool",
                    ],
                },
            },
        },
    }
    request_overrides = fake_llm_responses(tool_responses, request_overrides)
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        preset=preset,
        request_overrides=request_overrides,
    )
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert response == "Foo repeated twice is: foo foo"
    assert len(new_messages) == 5
    assert new_messages[0]["role"] == "system"
    assert new_messages[1]["role"] == "user"
    assert new_messages[2]["role"] == "assistant"
    assert new_messages[2]["message_type"] == "tool_call"
    assert new_messages[3]["role"] == "tool"
    assert new_messages[3]["message_type"] == "tool_response"
    assert new_messages[4]["role"] == "assistant"
    assert new_messages[4]["message_type"] == "content"


def test_request_with_tool_call_in_streaming_mode(
    test_config, tool_manager, provider_manager, preset_manager
):
    preset = preset_manager.presets["test"]
    tool_responses = [
        [
            AIMessageChunk(
                content="",
                additional_kwargs={"tool_call": {"name": "test_tool", "arguments": ""}},
            ),
            AIMessageChunk(
                content="",
                additional_kwargs={
                    "tool_call": {"arguments": '{\n  "word": "foo",\n  "repeats": 2\n}'}
                },
            ),
        ],
        [
            AIMessageChunk(content="Foo repeated twice is: "),
            AIMessageChunk(content="foo foo"),
        ],
    ]
    request_overrides = {
        "stream": True,
        "preset_overrides": {
            "model_customizations": {
                "model_kwargs": {
                    "tools": [
                        "test_tool",
                    ],
                },
            },
        },
    }
    request_overrides = fake_llm_responses(tool_responses, request_overrides)
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        preset=preset,
        request_overrides=request_overrides,
    )
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, _user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert success is True
    assert response == "Foo repeated twice is: foo foo"


def test_post_response_return_on_tool_call(
    test_config, tool_manager, provider_manager, preset_manager
):
    preset = preset_manager.presets["test"]
    tool_responses = [
        AIMessage(
            content="",
            additional_kwargs={
                "tool_call": {"name": "test_tool", "arguments": '{\n  "word": "foo"\n}'}
            },
        ),
    ]
    request_overrides = {
        "preset_overrides": {
            "metadata": {
                "return_on_tool_call": True,
            },
            "model_customizations": {
                "model_kwargs": {
                    "tools": [
                        "test_tool",
                    ],
                },
            },
        },
    }
    request_overrides = fake_llm_responses(tool_responses, request_overrides)
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        preset=preset,
        request_overrides=request_overrides,
    )
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert response == {"name": "test_tool", "arguments": {"word": "foo"}}
    assert len(new_messages) == 3
    assert new_messages[0]["role"] == "system"
    assert new_messages[1]["role"] == "user"
    assert new_messages[2]["role"] == "assistant"
    assert new_messages[2]["message_type"] == "tool_call"


def test_post_response_return_on_tool_response(
    test_config, tool_manager, provider_manager, preset_manager
):
    preset = preset_manager.presets["test"]
    tool_responses = [
        AIMessage(
            content="",
            additional_kwargs={
                "tool_call": {
                    "name": "test_tool",
                    "arguments": '{\n  "word": "foo",\n  "repeats": 2\n}',
                }
            },
        ),
        "Foo repeated twice is: foo foo",
    ]
    request_overrides = {
        "preset_overrides": {
            "metadata": {
                "return_on_tool_response": True,
            },
            "model_customizations": {
                "model_kwargs": {
                    "tools": [
                        "test_tool",
                    ],
                },
            },
        },
    }
    request_overrides = fake_llm_responses(tool_responses, request_overrides)
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        preset=preset,
        request_overrides=request_overrides,
    )
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert response["result"] == "foo foo"
    assert len(new_messages) == 4
    assert new_messages[0]["role"] == "system"
    assert new_messages[1]["role"] == "user"
    assert new_messages[2]["role"] == "assistant"
    assert new_messages[2]["message_type"] == "tool_call"
    assert new_messages[3]["role"] == "tool"
    assert new_messages[3]["message_type"] == "tool_response"


def test_post_response_multiple_tool_calls(
    test_config, tool_manager, provider_manager, preset_manager
):
    preset = preset_manager.presets["test"]
    tool_responses = [
        AIMessage(
            content="",
            additional_kwargs={
                "tool_call": {
                    "name": "test_tool",
                    "arguments": '{\n  "word": "foo",\n  "repeats": 2\n}',
                }
            },
        ),
        AIMessage(
            content="",
            additional_kwargs={
                "tool_call": {
                    "name": "test_tool",
                    "arguments": '{\n  "word": "foo",\n  "repeats": 2\n}',
                }
            },
        ),
        "Foo repeated twice is: foo foo",
    ]
    request_overrides = {
        "preset_overrides": {
            "model_customizations": {
                "model_kwargs": {
                    "tools": [
                        "test_tool",
                    ],
                },
            },
        },
    }
    request_overrides = fake_llm_responses(tool_responses, request_overrides)
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        preset=preset,
        request_overrides=request_overrides,
    )
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert response == "Foo repeated twice is: foo foo"
    assert len(new_messages) == 7
    assert new_messages[0]["role"] == "system"
    assert new_messages[1]["role"] == "user"
    assert new_messages[2]["role"] == "assistant"
    assert new_messages[2]["message_type"] == "tool_call"
    assert new_messages[3]["role"] == "tool"
    assert new_messages[3]["message_type"] == "tool_response"
    assert new_messages[4]["role"] == "assistant"
    assert new_messages[4]["message_type"] == "tool_call"
    assert new_messages[5]["role"] == "tool"
    assert new_messages[5]["message_type"] == "tool_response"
    assert new_messages[6]["role"] == "assistant"
    assert new_messages[6]["message_type"] == "content"


def test_post_response_forced_tool_call(
    test_config, tool_manager, provider_manager, preset_manager
):
    preset = preset_manager.presets["test"]
    tool_responses = [
        AIMessage(
            content="",
            additional_kwargs={
                "tool_call": {
                    "name": "test_tool",
                    "arguments": '{\n  "word": "foo",\n  "repeats": 2\n}',
                }
            },
        ),
        # These should NOT be called.
        AIMessage(
            content="",
            additional_kwargs={
                "tool_call": {
                    "name": "test_tool",
                    "arguments": '{\n  "word": "foo",\n  "repeats": 2\n}',
                }
            },
        ),
        "Foo repeated twice is: foo foo",
    ]
    request_overrides = {
        "preset_overrides": {
            "model_customizations": {
                "model_kwargs": {
                    "tools": [
                        "test_tool",
                    ],
                    "tool_call": {
                        "name": "test_tool",
                    },
                },
            },
        },
    }
    request_overrides = fake_llm_responses(tool_responses, request_overrides)
    request = make_api_request(
        test_config,
        tool_manager,
        provider_manager,
        preset_manager,
        preset=preset,
        request_overrides=request_overrides,
    )
    request.set_request_llm()
    new_messages, messages = request.prepare_ask_request()
    success, response_obj, user_message = request.call_llm(messages)
    response, new_messages = request.post_response(response_obj, new_messages)
    assert response["result"] == "foo foo"
    assert len(new_messages) == 4
    assert new_messages[0]["role"] == "system"
    assert new_messages[1]["role"] == "user"
    assert new_messages[2]["role"] == "assistant"
    assert new_messages[2]["message_type"] == "tool_call"
    assert new_messages[3]["role"] == "tool"
    assert new_messages[3]["message_type"] == "tool_response"


def test_request_exceeds_max_submission_tokens(
    test_config, tool_manager, provider_manager, preset_manager
):
    # Set max_submission_tokens to a low value
    request = make_api_request(
        test_config, tool_manager, provider_manager, preset_manager, max_submission_tokens=1
    )
    request.set_request_llm()
    with pytest.raises(Exception) as excinfo:
        request.prepare_ask_request()
    assert "over max submission tokens: 1" in str(excinfo.value)
