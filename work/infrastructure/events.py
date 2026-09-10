def build_payload(event: str, **kwargs) -> dict:
    data = {"event": event, **kwargs}
    return {k: str(v) for k, v in data.items() if v is not None}