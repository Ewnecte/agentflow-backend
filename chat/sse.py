"""SSE（Server-Sent Events）编码辅助。"""

import json


def format_sse(event_type: str, **data) -> str:
    """把事件封装成一条 SSE 数据帧，事件类型放 `type` 字段。"""
    payload = {'type': event_type, **data}
    return f'data: {json.dumps(payload, ensure_ascii=False)}\n\n'
