#!/usr/bin/env python

from chatgpt_wrapper.core.config import Config
from chatgpt_wrapper import ApiBackend

def test_api_backend_get_history():
    config = Config(profile='test')
    config.set('debug.log.enabled', True)
    gpt = ApiBackend(config, default_user_id=1)
    success, history, user_message = gpt.get_history(limit=3)
    if success:
        print("\nHistory:\n")
        for id, conversation in history.items():
            print(conversation['title'])
    assert success

if __name__ == '__main__':
    test_api_backend_get_history()
