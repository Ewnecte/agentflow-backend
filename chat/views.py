import json

from django.db.models import OuterRef, Subquery
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from rest_framework import viewsets

from .graph import graph
from .models import Conversation, Message
from .serializers import ConversationDetailSerializer, ConversationListSerializer
from .sse import format_sse

SYSTEM_PROMPT = '你是一个乐于助人的 AI 助手，请用中文回答用户的问题。'


def _auto_title(content: str) -> str:
    """用首条消息生成会话标题（截断 30 字）。"""
    text = content.replace('\n', ' ').strip()
    return text[:30] + ('…' if len(text) > 30 else '')


def _to_lc_message(msg: Message):
    if msg.role == 'user':
        return HumanMessage(content=msg.content)
    if msg.role == 'assistant':
        return AIMessage(content=msg.content)
    return SystemMessage(content=msg.content)


def _extract_text(chunk) -> str:
    """从流式 chunk 中抽取纯文本（兼容 string / 分块 content）。"""
    content = getattr(chunk, 'content', '')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get('type') == 'text':
                parts.append(item.get('text', ''))
        return ''.join(parts)
    return ''


class ConversationViewSet(viewsets.ModelViewSet):
    """会话 CRUD：列表 / 详情（含消息）/ 重命名 / 删除。"""

    queryset = Conversation.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationDetailSerializer

    def get_queryset(self):
        """列表时用子查询预取最后一条消息，避免逐条 N+1 查询。"""
        qs = super().get_queryset()
        if self.action == 'list':
            last = Message.objects.filter(conversation=OuterRef('pk')).order_by('-created_at')
            qs = qs.annotate(
                last_message_id=Subquery(last.values('id')[:1]),
                last_message_role=Subquery(last.values('role')[:1]),
                last_message_content=Subquery(last.values('content')[:1]),
                last_message_created_at=Subquery(last.values('created_at')[:1]),
            )
        return qs


@csrf_exempt
@require_POST
def chat_stream(request):
    """发送消息并以 SSE 流式返回 AI 回复。

    请求体：{"conversation_id": 1, "content": "你好"}（conversation_id 可省略，
    省略时新建会话）。
    事件流：token（增量文本） -> done（message_id / conversation_id）；
    出错时：error（message）。
    """
    try:
        data = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求体不是合法 JSON'}, status=400)

    content = (data.get('content') or '').strip()
    conversation_id = data.get('conversation_id')

    if not content:
        return JsonResponse({'error': 'content 不能为空'}, status=400)

    # 获取或创建会话
    if conversation_id:
        conversation = Conversation.objects.filter(pk=conversation_id).first()
        if conversation is None:
            return JsonResponse({'error': '会话不存在'}, status=404)
    else:
        conversation = Conversation.objects.create(title=_auto_title(content))

    # 保存用户消息，并刷新会话 updated_at（影响列表排序）
    Message.objects.create(conversation=conversation, role='user', content=content)
    conversation.save()

    # 组装上下文：系统提示 + 历史 + 本次用户消息
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages += [_to_lc_message(m) for m in conversation.messages.order_by('created_at')]

    def event_stream():
        buffer = ''
        try:
            for chunk, _meta in graph.stream({'messages': messages}, stream_mode='messages'):
                text = _extract_text(chunk)
                if text:
                    buffer += text
                    yield format_sse('token', content=text)

            msg = Message.objects.create(
                conversation=conversation, role='assistant', content=buffer
            )
            conversation.save()
            yield format_sse('done', message_id=msg.id, conversation_id=conversation.id)
        except Exception as exc:  # noqa: BLE001 —— 任何异常都以 error 事件返回
            # 已生成的部分内容也落库，避免历史里「只有用户消息、没有回复」的不一致
            if buffer:
                Message.objects.create(conversation=conversation, role='assistant', content=buffer)
                conversation.save()
            yield format_sse('error', message=str(exc))

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream; charset=utf-8')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
