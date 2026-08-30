from django.db import models


class Conversation(models.Model):
    """一次对话会话（单用户免登录，故暂不关联 User，后续加外键）。"""

    title = models.CharField(max_length=200, blank=True, default='新对话')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class Message(models.Model):
    """会话中的一条消息。"""

    ROLE_CHOICES = [
        ('user', 'user'),
        ('assistant', 'assistant'),
        ('system', 'system'),
    ]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    # 预留字段：token 用量、工具调用、思考过程等结构化信息
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:30]}'
