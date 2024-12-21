from django.db import models
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
import uuid

class CustomUser(AbstractUser):
    mobile_number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile_detail')
    is_online = models.BooleanField(default=False)


class ChatSession(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='user1_sessions'
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='user2_sessions'
    )
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("user1", "user2"),)
        verbose_name = 'Chat Session'

    def __str__(self):
        return f'{self.user1.username}_{self.user2.username}'

    @property
    def room_group_name(self):
        return f'chat_{self.id}'

    @staticmethod
    def chat_session_exists(user1, user2):
        return ChatSession.objects.filter(
            Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
        ).first()

    @staticmethod
    def create_if_not_exists(user1, user2):
        res = ChatSession.chat_session_exists(user1, user2)
        return res if res else ChatSession.objects.create(user1=user1, user2=user2)

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_session = models.ForeignKey(
        ChatSession, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        verbose_name='message_sender', 
        on_delete=models.CASCADE
    )
    message_detail = models.JSONField()

    class Meta:
        ordering = ['-message_detail__timestamp']

    def __str__(self):
        return str(self.message_detail.get("timestamp", "Unknown Timestamp"))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.chat_session.save()  # Update ChatSession timestamp

    @staticmethod
    def count_overall_unread_msg(user_id):
        total_unread_msg = 0
        user_sessions = ChatSession.objects.filter(
            Q(user1_id=user_id) | Q(user2_id=user_id)
        )
        for session in user_sessions:
            unread_count = ChatMessage.objects.filter(
                chat_session=session, 
                message_detail__read=False
            ).exclude(user_id=user_id).count()
            total_unread_msg += unread_count
        return total_unread_msg

    @staticmethod
    def mark_message_as_read(message_id):
        message = ChatMessage.objects.filter(id=message_id).first()
        if message:
            message.message_detail['read'] = True
            message.save(update_fields=['message_detail'])

    @staticmethod
    def mark_all_messages_as_read(room_id, user_id):
        messages = ChatMessage.objects.filter(
            chat_session_id=room_id, 
            message_detail__read=False
        ).exclude(user_id=user_id)
        for msg in messages:
            msg.message_detail['read'] = True
            msg.save(update_fields=['message_detail'])

    @staticmethod
    def mark_sender_message_inactive(message_id):
        message = ChatMessage.objects.filter(id=message_id).first()
        if message:
            message.message_detail['Sclr'] = True
            message.save(update_fields=['message_detail'])

    @staticmethod
    def mark_receiver_message_inactive(message_id):
        message = ChatMessage.objects.filter(id=message_id).first()
        if message:
            message.message_detail['Rclr'] = True
            message.save(update_fields=['message_detail'])
