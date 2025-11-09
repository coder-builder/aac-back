from rest_framework import serializers
from .models import Participant, TrialResponse, Preference


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = [
            'id', 'participant_id', 'name', 'phone_last4', 'age', 'gender', 'education', 'vision',
            'has_aac_experience', 'has_aac_education', 'consent_agreed',
            'block_order', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'participant_id', 'started_at', 'completed_at']


class TrialResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrialResponse
        fields = [
            'id', 'participant', 'trial_number', 'is_practice',
            'target_word', 'symbol_type', 'block_type',
            'presented_symbols', 'selected_symbol', 'is_correct',
            'reaction_time', 'responded_at'
        ]
        read_only_fields = ['id', 'responded_at']


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = [
            'id', 'participant', 'easier_to_understand', 'preference',
            'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']