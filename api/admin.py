from django.contrib import admin
from .models import Participant, TrialResponse, Preference, SymbolPreference


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['participant_id', 'name', 'age', 'gender', 'block_order', 'started_at', 'completed_at']
    list_filter = ['gender', 'block_order', 'has_aac_experience', 'vision']
    search_fields = ['participant_id', 'name', 'phone_last4']
    readonly_fields = ['participant_id', 'started_at', 'completed_at']
    ordering = ['-started_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('participant_id', 'name', 'phone_last4', 'age', 'gender', 'education')
        }),
        ('실험 정보', {
            'fields': ('vision', 'has_aac_experience', 'has_aac_education', 'block_order', 'consent_agreed')
        }),
        ('시간 정보', {
            'fields': ('started_at', 'completed_at')
        }),
    )


@admin.register(TrialResponse)
class TrialResponseAdmin(admin.ModelAdmin):
    list_display = ['participant', 'trial_number', 'target_word', 'symbol_type', 'is_correct', 'reaction_time',
                    'is_practice']
    list_filter = ['symbol_type', 'is_correct', 'is_practice', 'block_type']
    search_fields = ['participant__participant_id', 'participant__name', 'target_word']
    readonly_fields = ['responded_at']
    ordering = ['participant', 'trial_number']

    fieldsets = (
        ('참가자 정보', {
            'fields': ('participant',)
        }),
        ('시행 정보', {
            'fields': ('trial_number', 'is_practice', 'target_word', 'symbol_type', 'block_type')
        }),
        ('응답 데이터', {
            'fields': ('selected_symbol', 'is_correct', 'reaction_time', 'error_count')
        }),
        ('기타', {
            'fields': ('presented_symbols', 'responded_at')
        }),
    )


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ['participant', 'easier_to_understand', 'preference', 'created_at']
    list_filter = ['easier_to_understand', 'preference']
    search_fields = ['participant__participant_id', 'participant__name', 'reason']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('참가자 정보', {
            'fields': ('participant',)
        }),
        ('선호도 응답', {
            'fields': ('easier_to_understand', 'preference', 'reason')
        }),
        ('기타', {
            'fields': ('created_at',)
        }),
    )


# 🆕 단어별 선호도 관리
@admin.register(SymbolPreference)
class SymbolPreferenceAdmin(admin.ModelAdmin):
    list_display = ['participant', 'target_word', 'ai_position', 'chosen', 'chosen_type', 'created_at']
    list_filter = ['target_word', 'chosen_type', 'ai_position']
    search_fields = ['participant__participant_id', 'participant__name', 'target_word']
    readonly_fields = ['created_at']
    ordering = ['participant', 'target_word']
    list_per_page = 100

    fieldsets = (
        ('참가자 정보', {
            'fields': ('participant',)
        }),
        ('단어 정보', {
            'fields': ('target_word',)
        }),
        ('선택 정보', {
            'fields': ('ai_position', 'chosen', 'chosen_type')
        }),
        ('기타', {
            'fields': ('created_at',)
        }),
    )

    # 참가자별로 보기 쉽게
    list_display_links = ['participant', 'target_word']

    # 참가자별 필터링 (사이드바)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('participant')