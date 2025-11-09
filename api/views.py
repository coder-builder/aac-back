from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import Participant, TrialResponse, Preference, SymbolPreference
from .serializers import ParticipantSerializer, TrialResponseSerializer, PreferenceSerializer


def generate_participant_id():
    """참가자 ID 자동 생성 (P0001 형식)"""
    last_participant = Participant.objects.order_by('-id').first()
    if last_participant:
        last_id = int(last_participant.participant_id[1:])
        new_id = f"P{str(last_id + 1).zfill(4)}"
    else:
        new_id = "P0001"
    return new_id


@api_view(['POST'])
@transaction.atomic
def complete_experiment(request):
    """
    실험 완료 - 모든 데이터를 한 번에 저장
    """
    try:
        data = request.data
        print('📥 Received data keys:', data.keys())

        # 1. Demographic 데이터 추출
        demographic_data = data.get('demographic')
        if not demographic_data:
            return Response(
                {'error': 'demographic data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f'✅ Demographic data: {demographic_data}')
        print(f'📞 Phone last 4: {demographic_data.get("phone_last4")}')

        # 🆕 시작/완료 시간 (프론트에서 받음)
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        print(f'⏰ Start time: {start_time}')
        print(f'⏰ End time: {end_time}')

        # 시간 파싱
        started_at = parse_datetime(start_time) if start_time else timezone.now()
        completed_at = parse_datetime(end_time) if end_time else None

        # 2. Participant 생성
        participant = Participant.objects.create(
            participant_id=generate_participant_id(),
            name=demographic_data.get('name', ''),
            phone_last4=demographic_data.get('phone_last4', ''),  # ← phone_last4 직접 사용!
            age=int(demographic_data.get('age', 0)),
            gender=demographic_data.get('gender', 'male'),
            vision=demographic_data.get('vision', 'normal'),
            education=demographic_data.get('education', ''),
            has_aac_experience=demographic_data.get('has_aac_experience', False),
            has_aac_education=demographic_data.get('has_aac_education', False),
            consent_agreed=True,
            block_order=demographic_data.get('block_order', 1),
            started_at=started_at,  # ← 프론트 시간 사용!
            completed_at=completed_at  # ← 프론트 시간 사용!
        )

        print(f'✅ Created participant: {participant.participant_id}')
        print(f'✅ Phone: {participant.phone_last4}')

        # 3. Practice Trials 저장
        practice_results = data.get('practice_results', [])
        print(f'📝 Saving {len(practice_results)} practice trials...')

        for idx, trial_data in enumerate(practice_results, start=1):
            TrialResponse.objects.create(
                participant=participant,
                trial_number=idx,
                is_practice=True,
                target_word=trial_data.get('target_word', ''),
                symbol_type=trial_data.get('symbol_type', ''),
                block_type=trial_data.get('symbol_type', ''),
                presented_symbols=[],
                selected_symbol=trial_data.get('selected_symbol', ''),
                is_correct=trial_data.get('is_correct', False),
                reaction_time=trial_data.get('reaction_time', 0),
                error_count=trial_data.get('error_count', 0)
            )

        # 4. Experiment Trials 저장
        trial_results = data.get('trial_results', [])
        print(f'📝 Saving {len(trial_results)} experiment trials...')

        for idx, trial_data in enumerate(trial_results, start=1):
            TrialResponse.objects.create(
                participant=participant,
                trial_number=idx,
                is_practice=False,
                target_word=trial_data.get('target_word', ''),
                symbol_type=trial_data.get('symbol_type', ''),
                block_type=trial_data.get('symbol_type', ''),
                presented_symbols=[],
                selected_symbol=trial_data.get('selected_symbol', ''),
                is_correct=trial_data.get('is_correct', False),
                reaction_time=trial_data.get('reaction_time', 0),
                error_count=trial_data.get('error_count', 0)
            )

        print(f'🎉 All data saved successfully for {participant.participant_id}')

        return Response({
            'message': 'Experiment completed successfully',
            'participant_id': participant.participant_id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f'❌ Error completing experiment: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_participant(request):
    """참가자 생성 (필요시)"""
    try:
        data = request.data
        participant_id = generate_participant_id()

        participant = Participant.objects.create(
            participant_id=participant_id,
            name=data.get('name', ''),
            phone_last4=data.get('phone_last4', ''),
            age=data.get('age', 0),
            gender=data.get('gender', 'male'),
            vision=data.get('vision', 'normal'),
            education=data.get('education', ''),
            has_aac_experience=data.get('has_aac_experience', False),
            has_aac_education=data.get('has_aac_education', False),
            consent_agreed=data.get('consent_agreed', False),
            block_order=data.get('block_order', 1)
        )

        serializer = ParticipantSerializer(participant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_participants(request):
    """모든 참가자 조회"""
    participants = Participant.objects.all()
    serializer = ParticipantSerializer(participants, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_participant(request, participant_id):
    """특정 참가자 조회"""
    try:
        participant = Participant.objects.get(participant_id=participant_id)
        serializer = ParticipantSerializer(participant)
        return Response(serializer.data)
    except Participant.DoesNotExist:
        return Response({'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def save_trial(request):
    """단일 시행 저장 (필요시)"""
    try:
        data = request.data
        trial = TrialResponse.objects.create(
            participant_id=data.get('participant_id'),
            trial_number=data.get('trial_number'),
            is_practice=data.get('is_practice', False),
            target_word=data.get('target_word'),
            symbol_type=data.get('symbol_type'),
            block_type=data.get('block_type'),
            presented_symbols=data.get('presented_symbols', []),
            selected_symbol=data.get('selected_symbol'),
            is_correct=data.get('is_correct'),
            reaction_time=data.get('reaction_time'),
            error_count=data.get('error_count', 0)
        )
        serializer = TrialResponseSerializer(trial)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_trials(request, participant_id):
    """특정 참가자의 모든 시행 조회"""
    try:
        participant = Participant.objects.get(participant_id=participant_id)
        trials = TrialResponse.objects.filter(participant=participant)
        serializer = TrialResponseSerializer(trials, many=True)
        return Response(serializer.data)
    except Participant.DoesNotExist:
        return Response({'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def save_preference(request):
    """선호도 저장 (필요시)"""
    try:
        data = request.data
        participant = Participant.objects.get(id=data.get('participant_id'))

        preference = Preference.objects.create(
            participant=participant,
            easier_to_understand=data.get('easier_to_understand'),
            preference=data.get('preference'),
            reason=data.get('reason', '')
        )

        serializer = PreferenceSerializer(preference)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Participant.DoesNotExist:
        return Response({'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_preference(request, participant_id):
    """특정 참가자의 선호도 조회"""
    try:
        participant = Participant.objects.get(participant_id=participant_id)
        preference = Preference.objects.get(participant=participant)
        serializer = PreferenceSerializer(preference)
        return Response(serializer.data)
    except (Participant.DoesNotExist, Preference.DoesNotExist):
        return Response({'error': 'Data not found'}, status=status.HTTP_404_NOT_FOUND)


# ========================================
# 🆕 단어별 선호도 API
# ========================================

@api_view(['POST'])
def submit_symbol_preferences(request):
    """
    단어별 상징 선호도 제출

    POST /api/submit-symbol-preferences/

    Body:
    {
        "participant_id": "P0001",
        "preferences": [7개 배열]
    }
    """
    participant_id = request.data.get('participant_id')
    preferences = request.data.get('preferences', [])

    print(f'📥 Symbol preferences for {participant_id}: {len(preferences)} items')

    # 검증
    if not participant_id:
        return Response(
            {'error': 'participant_id가 필요합니다'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not preferences or len(preferences) != 7:
        return Response(
            {'error': '7개 단어에 대한 선호도가 필요합니다'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 참가자 확인
    try:
        participant = Participant.objects.get(participant_id=participant_id)
    except Participant.DoesNotExist:
        return Response(
            {'error': '참가자를 찾을 수 없습니다'},
            status=status.HTTP_404_NOT_FOUND
        )

    # 기존 선호도 삭제 (재제출 시)
    deleted_count = SymbolPreference.objects.filter(participant=participant).delete()[0]
    if deleted_count > 0:
        print(f'⚠️ Deleted {deleted_count} existing preferences')

    # 새로운 선호도 저장
    created_preferences = []
    try:
        for pref in preferences:
            symbol_pref = SymbolPreference.objects.create(
                participant=participant,
                target_word=pref.get('target_word'),
                ai_position=pref.get('ai_position'),
                chosen=pref.get('chosen'),
                chosen_type=pref.get('chosen_type')
            )
            created_preferences.append({
                'target_word': symbol_pref.target_word,
                'chosen_type': symbol_pref.chosen_type
            })
            print(f'✅ Saved: {symbol_pref.target_word} → {symbol_pref.chosen_type}')

    except Exception as e:
        print(f'❌ Error saving preferences: {str(e)}')
        return Response(
            {'error': f'저장 오류: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    print(f'🎉 All {len(created_preferences)} preferences saved!')

    return Response({
        'message': '단어별 선호도가 성공적으로 저장되었습니다',
        'participant_id': participant_id,
        'count': len(created_preferences),
        'preferences': created_preferences
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_symbol_preferences(request, participant_id):
    """
    특정 참가자의 단어별 선호도 조회

    GET /api/symbol-preferences/<participant_id>/
    """
    try:
        participant = Participant.objects.get(participant_id=participant_id)
    except Participant.DoesNotExist:
        return Response(
            {'error': '참가자를 찾을 수 없습니다'},
            status=status.HTTP_404_NOT_FOUND
        )

    preferences = SymbolPreference.objects.filter(participant=participant)

    data = [{
        'target_word': pref.target_word,
        'ai_position': pref.ai_position,
        'chosen': pref.chosen,
        'chosen_type': pref.chosen_type,
        'created_at': pref.created_at
    } for pref in preferences]

    return Response({
        'participant_id': participant_id,
        'count': len(data),
        'preferences': data
    })


@api_view(['GET'])
def get_preference_summary(request):
    """
    전체 선호도 요약 통계

    GET /api/preference-summary/
    """
    total_responses = SymbolPreference.objects.count()

    # 단어별 통계
    word_stats = {}
    words = ["안녕하세요", "고마워요", "미안합니다", "좋아요", "싫어요", "도와주세요", "배고파요"]

    for word in words:
        word_prefs = SymbolPreference.objects.filter(target_word=word)
        ai_count = word_prefs.filter(chosen_type='ai').count()
        kaac_count = word_prefs.filter(chosen_type='kaac').count()
        similar_count = word_prefs.filter(chosen_type='similar').count()

        word_stats[word] = {
            'ai': ai_count,
            'kaac': kaac_count,
            'similar': similar_count,
            'total': word_prefs.count()
        }

    # 전체 통계
    overall_stats = {
        'ai': SymbolPreference.objects.filter(chosen_type='ai').count(),
        'kaac': SymbolPreference.objects.filter(chosen_type='kaac').count(),
        'similar': SymbolPreference.objects.filter(chosen_type='similar').count()
    }

    return Response({
        'total_responses': total_responses,
        'total_participants': SymbolPreference.objects.values('participant').distinct().count(),
        'overall_stats': overall_stats,
        'word_stats': word_stats
    })