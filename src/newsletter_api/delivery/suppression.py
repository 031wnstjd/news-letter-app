from __future__ import annotations


class SuppressionPolicy:
    def __init__(self) -> None:
        self.soft_bounce_counts: dict[str, int] = {}
        self.suppressed: set[str] = set()

    def apply_event(self, email: str, event_type: str) -> bool:
        if event_type == "hard_bounce":
            self.suppressed.add(email)
            return True
        if event_type == "soft_bounce":
            self.soft_bounce_counts[email] = self.soft_bounce_counts.get(email, 0) + 1
            if self.soft_bounce_counts[email] >= 3:
                self.suppressed.add(email)
                return True
            return False
        return False


policy = SuppressionPolicy()
