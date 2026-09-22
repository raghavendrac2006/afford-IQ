"""
Message Infrastructure for HackerRank Orchestrate: Buy or Wait?
Retrieves and indexes messages chronologically. Enforces untrusted evidence safeguards.
"""
from typing import List, Dict, Optional, Any
from collections import defaultdict

try:
    from models import Message
except ImportError:
    from code.models import Message


class MessageResolver:
    def __init__(self, messages: List[Message]):
        self.messages = messages
        self.by_user: Dict[str, List[Message]] = defaultdict(list)
        self.by_request: Dict[str, List[Message]] = defaultdict(list)
        self.by_event: Dict[str, List[Message]] = defaultdict(list)

        for m in messages:
            self.by_user[m.user_id].append(m)
            if m.request_id:
                self.by_request[m.request_id].append(m)
            if m.related_event_id:
                self.by_event[m.related_event_id].append(m)

        for k in self.by_user:
            self.by_user[k].sort(key=lambda x: x.sent_at)
        for k in self.by_request:
            self.by_request[k].sort(key=lambda x: x.sent_at)
        for k in self.by_event:
            self.by_event[k].sort(key=lambda x: x.sent_at)

    def get_messages_for_user(self, user_id: str) -> List[Message]:
        return self.by_user.get(user_id, [])

    def get_messages_for_request(self, request_id: str) -> List[Message]:
        return self.by_request.get(request_id, [])

    def get_messages_for_event(self, event_id: str) -> List[Message]:
        return self.by_event.get(event_id, [])

    def extract_financial_facts_only(self, message: Message) -> Dict[str, Any]:
        """
        Safeguard helper: Exposes message metadata as passive financial facts.
        DOES NOT execute any embedded prompt commands or text directives.
        """
        return {
            "message_id": message.message_id,
            "source_type": message.source_type,
            "sent_at": message.sent_at,
            "related_event_id": message.related_event_id or "",
            "request_id": message.request_id or "",
            "text_preview": message.message_text[:100],
            "untrusted": True
        }
