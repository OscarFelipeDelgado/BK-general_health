from django.urls import path
from mental_health.views import check_profile, complete_intervention, evaluate_emotional_state, get_dashboard, get_history, get_profile, get_questions, register_user, save_profile, save_reflection, update_profile

urlpatterns = [
    path('evaluate/', evaluate_emotional_state, name='evaluate_emotional_state'),
    path('history/', get_history, name='get_history'),
    path('dashboard/', get_dashboard, name='dashboard'),
    path('questions/', get_questions, name='get_questions'),
    path('profile/', save_profile, name='save_profile'),
    path('check-profile/', check_profile, name='check_profile'),
    path('register/', register_user, name='register_user'),
    path('profile/detail/', get_profile, name='get_profile'),
    path('profile/update/', update_profile, name='update_profile'),
    path('intervention/complete/', complete_intervention, name='complete_intervention'),
    path('intervention/reflection/', save_reflection, name='save_reflection'),

]