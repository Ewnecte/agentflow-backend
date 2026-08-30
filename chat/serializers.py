from rest_framework import serializers

from .models import Conversation, Message


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
        msg = obj.messages.last()
        return MessageSerializer(msg).data if msg else None


class ConversationDetailSerializer(serializers.ModelSerializer):
    """会话详情：附带全部消息。"""

    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages']
