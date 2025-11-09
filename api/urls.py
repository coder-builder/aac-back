from django.urls import path
from . import views

urlpatterns = [
    # 실험 완료 (메인!)
    path('complete-experiment/', views.complete_experiment, name='complete_experiment'),

    # 참가자 관련
    path('participants/', views.create_participant, name='create_participant'),
    path('participants/list/', views.get_participants, name='get_participants'),
    path('participants/<str:participant_id>/', views.get_participant, name='get_participant'),

    # 시행 관련
    path('trials/', views.save_trial, name='save_trial'),
    path('trials/<str:participant_id>/', views.get_trials, name='get_trials'),

    # 선호도 관련 (기존)
    path('preference/', views.save_preference, name='save_preference'),
    path('preference/<str:participant_id>/', views.get_preference, name='get_preference'),

    # 🆕 단어별 선호도 (새로 추가!)
    path('submit-symbol-preferences/', views.submit_symbol_preferences, name='submit_symbol_preferences'),
    path('symbol-preferences/<str:participant_id>/', views.get_symbol_preferences, name='get_symbol_preferences'),
    path('preference-summary/', views.get_preference_summary, name='preference_summary'),
]