from rest_framework import serializers

from .models import Conversation, Message


def _iso(value):
    """把带时区的 datetime 格式化成与 DRF 一致的 ISO-8601（UTC 用 Z 结尾）。"""
    if value is None:
        return None
    text = value.isoformat()
    return text[:-6] + 'Z' if text.endswith('+00:00') else text


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = fields


class ConversationListSerializer(serializers.ModelSerializer):
    """会话列表：附带最后一条消息的预览。"""

    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'last_message']

    def get_last_message(self, obj):
        # 列表视图已通过子查询注解出最后一条消息；未注解的路径兜底走一次查询
        if not hasattr(obj, 'last_message_id'):
            msg = obj.messages.last()
            return MessageSerializer(msg).data if msg else None
        if obj.last_message_id is None:
            return None
        return {
            'id': obj.last_message_id,
            'role': obj.last_message_role,
            'content': obj.last_message_content,
            'created_at': _iso(obj.last_message_created_at),
        }


class ConversationDetailSerializer(serializers.ModelSerializer):
    """会话详情：附带全部消息。"""

    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages']
