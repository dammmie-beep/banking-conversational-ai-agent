# # app/memory.py
# from collections import deque
# from typing import Dict, List

# class ConversationMemory:
#     def __init__(self, max_turns: int = 10):
#         self.max_messages = max_turns * 2
#         self.history: deque = deque(maxlen=self.max_messages)

#     def add_user(self, content: str):
#         self.history.append({"role": "user", "content": content})

#     def add_assistant(self, content: str):
#         self.history.append({"role": "assistant", "content": content})

#     def get_history(self) -> List[Dict]:         # ← List[Dict] not list[dict]
#         return list(self.history)

#     def clear(self):
#         self.history.clear()


# session_store: Dict[str, ConversationMemory] = {}  # ← Dict not dict

# def get_session(session_id: str) -> ConversationMemory:
#     if session_id not in session_store:
#         session_store[session_id] = ConversationMemory(max_turns=10)
#     return session_store[session_id]

from collections import deque
from typing import Dict, List

class ConversationMemory:
    def __init__(self, max_turns: int = 10):
        self.max_messages = max_turns * 2
        self.history: deque = deque(maxlen=self.max_messages)
        self.state: Dict = {}

    def add_user(self, content: str):
        self.history.append({"role": "user", "content": content})

    def add_assistant(self, content: str):
        self.history.append({"role": "assistant", "content": content})

    def get_history(self) -> List[Dict]:
        return list(self.history)

    def set_state(self, key: str, value):
        self.state[key] = value

    def get_state(self, key: str, default=None):
        return self.state.get(key, default)

    def clear(self):
        self.history.clear()
        self.state.clear()


session_store: Dict[str, ConversationMemory] = {}

def get_session(session_id: str) -> ConversationMemory:
    if session_id not in session_store:
        session_store[session_id] = ConversationMemory(max_turns=10)
    return session_store[session_id]