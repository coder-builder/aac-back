# backend/export_to_excel.py
# 모든 데이터를 엑셀로 내보내기 (개선 버전!)

import os
import django
import pandas as pd
from datetime import datetime

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Participant, TrialResponse, Preference, SymbolPreference
from django.db.models import Avg


def calculate_duration(started_at, completed_at):
    """소요 시간 계산 (분 단위)"""
    if started_at and completed_at:
        duration = completed_at - started_at
        return round(duration.total_seconds() / 60, 2)  # 분 단위
    return None


def export_all_data():
    """모든 데이터를 하나의 엑셀 파일로 내보내기"""

    # 파일명: 실험데이터_날짜.xlsx
    filename = f"실험데이터_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    print(f"📊 데이터를 엑셀로 내보내는 중...")
    print(f"파일명: {filename}")

    # ExcelWriter 생성
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:

        # 1. 참가자 정보 시트
        participants = Participant.objects.all()
        participant_data = []

        for p in participants:
            # 총 소요시간 계산
            duration = calculate_duration(p.started_at, p.completed_at)

            participant_data.append({
                '참가자ID': p.participant_id,
                '이름': p.name,
                '연락처뒷자리': p.phone_last4,
                '나이': p.age,
                '성별': p.get_gender_display(),
                '교육수준': p.education,
                '시력': p.get_vision_display(),
                'AAC경험': 'O' if p.has_aac_experience else 'X',
                'AAC교육': 'O' if p.has_aac_education else 'X',
                '블록순서': 'AI먼저' if p.block_order == 1 else 'KAAC먼저',
                '총소요시간(분)': duration if duration else '',
            })

        df_participants = pd.DataFrame(participant_data)
        df_participants.to_excel(writer, sheet_name='참가자정보', index=False)
        print(f"✅ 참가자 정보: {len(df_participants)}명")

        # 2. 시행 데이터 시트 (본실험만!)
        trials = TrialResponse.objects.select_related('participant').filter(is_practice=False)

        trial_data = []
        for t in trials:
            trial_data.append({
                '참가자ID': t.participant.participant_id,
                '참가자명': t.participant.name,
                '시행번호': t.trial_number,
                '목표단어': t.target_word,
                '상징유형': 'AI' if t.symbol_type == 'ai' else 'KAAC',
                '블록유형': t.block_type,
                '선택상징': t.selected_symbol,
                '정답여부': '정답' if t.is_correct else '오답',
                '반응시간ms': t.reaction_time,
                '오답횟수': t.error_count,
            })

        df_trials = pd.DataFrame(trial_data)
        df_trials.to_excel(writer, sheet_name='시행데이터_본실험만', index=False)
        print(f"✅ 시행 데이터 (본실험만): {len(df_trials)}개")

        # 3. 전체 선호도 데이터 시트
        preferences = Preference.objects.select_related('participant').all()

        pref_data = []
        for p in preferences:
            easier_map = {'ai': 'AI', 'kaac': 'KAAC', 'similar': '비슷함'}
            pref_map = {'ai': 'AI', 'kaac': 'KAAC', 'similar': '비슷함'}

            pref_data.append({
                '참가자ID': p.participant.participant_id,
                '참가자명': p.participant.name,
                '이해하기쉬운것': easier_map.get(p.easier_to_understand, ''),
                '선호': pref_map.get(p.preference, ''),
                '이유': p.reason,
            })

        df_preferences = pd.DataFrame(pref_data)

        if not df_preferences.empty:
            df_preferences.to_excel(writer, sheet_name='전체선호도', index=False)
            print(f"✅ 전체 선호도 데이터: {len(df_preferences)}개")
        else:
            print(f"⚠️ 전체 선호도 데이터 없음 (0개)")

        # 4. 단어별 선호도 시트
        symbol_prefs = SymbolPreference.objects.select_related('participant').all()

        symbol_pref_data = []
        for sp in symbol_prefs:
            type_map = {'ai': 'AI', 'kaac': 'KAAC', 'similar': '비슷함'}

            symbol_pref_data.append({
                '참가자ID': sp.participant.participant_id,
                '참가자명': sp.participant.name,
                '대상단어': sp.target_word,
                'AI위치': '왼쪽' if sp.ai_position == 'left' else '오른쪽',
                '선택': sp.chosen,
                '선택유형': type_map.get(sp.chosen_type, sp.chosen_type),
            })

        df_symbol_prefs = pd.DataFrame(symbol_pref_data)

        if not df_symbol_prefs.empty:
            df_symbol_prefs.to_excel(writer, sheet_name='단어별선호도', index=False)
            print(f"✅ 단어별 선호도 데이터: {len(df_symbol_prefs)}개")
        else:
            print(f"⚠️ 단어별 선호도 데이터 없음 (0개)")

        # 5. 단어별 통계 요약 시트
        words = ["안녕하세요", "고마워요", "미안합니다", "좋아요", "싫어요", "도와주세요", "배고파요"]
        word_summary = []

        for word in words:
            word_prefs = SymbolPreference.objects.filter(target_word=word)
            ai_count = word_prefs.filter(chosen_type='ai').count()
            kaac_count = word_prefs.filter(chosen_type='kaac').count()
            similar_count = word_prefs.filter(chosen_type='similar').count()
            total = word_prefs.count()

            if total > 0:
                word_summary.append({
                    '단어': word,
                    'AI선택': ai_count,
                    'KAAC선택': kaac_count,
                    '비슷함': similar_count,
                    '총응답': total,
                    'AI비율%': round(ai_count / total * 100, 1) if total > 0 else 0,
                    'KAAC비율%': round(kaac_count / total * 100, 1) if total > 0 else 0,
                    '비슷함비율%': round(similar_count / total * 100, 1) if total > 0 else 0,
                })

        df_word_summary = pd.DataFrame(word_summary)
        if not df_word_summary.empty:
            df_word_summary.to_excel(writer, sheet_name='단어별통계', index=False)
            print(f"✅ 단어별 통계: {len(df_word_summary)}개")
        else:
            print(f"⚠️ 단어별 통계 없음 (선호도 데이터 없음)")

        # 6. 요약 통계 시트
        summary_data = []

        for participant in Participant.objects.all():
            # 본 실험 시행만 (연습 제외!)
            exp_trials = TrialResponse.objects.filter(
                participant=participant,
                is_practice=False
            )

            if exp_trials.exists():
                total = exp_trials.count()
                correct = exp_trials.filter(is_correct=True).count()
                accuracy = (correct / total) * 100
                avg_rt = exp_trials.aggregate(avg_rt=Avg('reaction_time'))['avg_rt']

                # AI vs KAAC
                ai_trials = exp_trials.filter(symbol_type='ai')
                kaac_trials = exp_trials.filter(symbol_type='kaac')

                ai_correct = ai_trials.filter(is_correct=True).count()
                ai_total = ai_trials.count()
                ai_accuracy = (ai_correct / ai_total) * 100 if ai_total > 0 else 0
                ai_rt = ai_trials.aggregate(avg_rt=Avg('reaction_time'))['avg_rt'] or 0

                kaac_correct = kaac_trials.filter(is_correct=True).count()
                kaac_total = kaac_trials.count()
                kaac_accuracy = (kaac_correct / kaac_total) * 100 if kaac_total > 0 else 0
                kaac_rt = kaac_trials.aggregate(avg_rt=Avg('reaction_time'))['avg_rt'] or 0

                # 전체 선호도
                try:
                    pref = Preference.objects.get(participant=participant)
                    easier_map = {'ai': 'AI', 'kaac': 'KAAC', 'similar': '비슷함'}
                    pref_map = {'ai': 'AI', 'kaac': 'KAAC', 'similar': '비슷함'}
                    easier = easier_map.get(pref.easier_to_understand, '')
                    preference = pref_map.get(pref.preference, '')
                except Preference.DoesNotExist:
                    easier = ''
                    preference = ''

                # 단어별 선호도 요약
                symbol_prefs = SymbolPreference.objects.filter(participant=participant)
                ai_pref_count = symbol_prefs.filter(chosen_type='ai').count()
                kaac_pref_count = symbol_prefs.filter(chosen_type='kaac').count()
                similar_pref_count = symbol_prefs.filter(chosen_type='similar').count()

                # 총 소요시간
                duration = calculate_duration(participant.started_at, participant.completed_at)

                summary_data.append({
                    '참가자ID': participant.participant_id,
                    '참가자명': participant.name,
                    '나이': participant.age,
                    '성별': participant.get_gender_display(),
                    '블록순서': 'AI먼저' if participant.block_order == 1 else 'KAAC먼저',
                    '총소요시간(분)': duration if duration else '',
                    '전체정확도%': round(accuracy, 2),
                    '평균반응시간ms': round(avg_rt, 2),
                    'AI정확도%': round(ai_accuracy, 2),
                    'AI평균RT': round(ai_rt, 2),
                    'KAAC정확도%': round(kaac_accuracy, 2),
                    'KAAC평균RT': round(kaac_rt, 2),
                    '전체_이해쉬운것': easier,
                    '전체_선호': preference,
                    '단어별_AI선호수': ai_pref_count,
                    '단어별_KAAC선호수': kaac_pref_count,
                    '단어별_비슷함수': similar_pref_count,
                })

        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='요약통계', index=False)
        print(f"✅ 요약 통계: {len(df_summary)}명")

    print(f"\n🎉 완료! 파일 저장됨: {filename}")
    print(f"📁 위치: {os.path.abspath(filename)}")


if __name__ == '__main__':
    export_all_data()