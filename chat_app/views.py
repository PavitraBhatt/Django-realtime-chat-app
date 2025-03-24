from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy
from .models import ChatSession, ChatMessage
from .forms import MobileLoginForm
from chat_app.models import CustomUser
from .decorators import custom_login_required
     
def home(request):
    unread_msg = ChatMessage.count_overall_unread_msg(request.user.id)
    return render(request, 'chat/home.html', {"unread_msg": unread_msg})

@custom_login_required
def create_friend(request):
    user_1 = request.user
    if request.GET.get('id'):
        user2_id = request.GET.get('id')
        user_2 = get_object_or_404(CustomUser, id=user2_id)
        created = ChatSession.create_if_not_exists(user_1, user_2)
        if created:
            messages.success(request, f'{user_2.username} successfully added to your chat list!')
        else:
            messages.info(request, f'{user_2.username} is already in your chat list.')
        return redirect(reverse_lazy('create_friend'))

    user_all_friends = ChatSession.objects.filter(Q(user1=user_1) | Q(user2=user_1))
    user_list = {friend.user1.id for friend in user_all_friends}.union({friend.user2.id for friend in user_all_friends})
    all_users = CustomUser.objects.exclude(Q(username=user_1.username) | Q(id__in=user_list))
    return render(request, 'chat/create_friend.html', {'all_user': all_users})


@custom_login_required
def friend_list(request):
    user_inst = request.user
    user_all_friends = ChatSession.objects.filter(Q(user1=user_inst) | Q(user2=user_inst)).select_related('user1', 'user2').order_by('-updated_on')

    all_friends = [
        {
            "user_name": friend.user2.username if friend.user1 == user_inst else friend.user1.username,
            "room_name": friend.room_group_name,
            "un_read_msg_count": ChatMessage.objects.filter(
                chat_session=friend, message_detail__read=False
            ).exclude(user=user_inst).count(),
            "status": (friend.user2 if friend.user1 == user_inst else friend.user1).profile_detail.is_online,
            "user_id": (friend.user2 if friend.user1 == user_inst else friend.user1).id,
        }
        for friend in user_all_friends
    ]

    return render(request, 'chat/friend_list.html', {'user_list': all_friends})


@custom_login_required
def start_chat(request, room_name):
    current_user = request.user
    room_id = room_name[5:]
    chat_session = ChatSession.objects.filter(id=room_id).filter(
        Q(user1=current_user) | Q(user2=current_user)
    ).first()

    if chat_session:
        opposite_user = chat_session.user2 if chat_session.user1 == current_user else chat_session.user1
        messages = ChatMessage.objects.filter(chat_session=chat_session).order_by('message_detail__timestamp')
        return render(request, 'chat/start_chat.html', {'room_name': room_name, 'opposite_user': opposite_user, 'fetch_all_message': messages})

    return HttpResponse("You don't have permission to chat with this user!")


def get_last_message(request):
    session_id = request.GET.get('room_id')
    messages = ChatMessage.objects.filter(chat_session__id=session_id).order_by('-message_detail__timestamp')[:10]
    if messages.exists():
        return HttpResponse(messages.last())
    return HttpResponse("No messages found.")


def mobile_login(request):
    if request.method == 'POST':
        form = MobileLoginForm(request.POST)
        if form.is_valid():
            mobile_number = form.cleaned_data['mobile_number']
            password = form.cleaned_data['password']
            user = authenticate(request, username=mobile_number, password=password)
            if user:
                login(request, user)
                return redirect('home_page')  # Ensure this redirects to the home page
            else:
                messages.error(request, 'Invalid mobile number or password.')
    else:
        form = MobileLoginForm()
    return render(request, 'chat/mobile_login.html', {'form': form})