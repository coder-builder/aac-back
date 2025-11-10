from django.db import models
from django.utils import timezone


class Participant(models.Model):
    """참가자 정보"""
    # 기본 정보
    participant_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, verbose_name="이름")
    phone = models.CharField(max_length=11, verbose_name="전화번호")  # 전체 번호 저장
    phone_last4 = models.CharField(max_length=4, verbose_name="연락처 뒷자리")  # 하위 호환
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[
        ('male', '남성'),
        ('female', '여성')
    ])
    education = models.CharField(max_length=50, blank=False)  # 필수값으로 변경
    vision = models.CharField(max_length=20, choices=[
        ('normal', '정상'),
        ('corrected', '교정')
    ], verbose_name="시력")

    # AAC 관련 경험
    has_aac_experience = models.BooleanField(default=False)
    has_aac_education = models.BooleanField(default=False)

    # 실험 정보
    consent_agreed = models.BooleanField(default=False)

    # 시간 필드 - 수동 설정 가능!
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    # 블록 순서 역균형화 (1: AI먼저, 2: 기존먼저)
    block_order = models.IntegerField(choices=[(1, 'AI first'), (2, 'Existing first')])

    class Meta:
        db_table = 'participants'
        ordering = ['-started_at']

    def __str__(self):
        return f"Participant {self.participant_id}"


class TrialResponse(models.Model):
    """각 시행의 응답 데이터"""
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='responses')

    # 시행 정보
    trial_number = models.IntegerField()
    is_practice = models.BooleanField(default=False)

    # 자극 정보
    target_word = models.CharField(max_length=20)
    symbol_type = models.CharField(max_length=10, choices=[
        ('ai', 'AI 생성'),
        ('kaac', 'KAAC')
    ])
    block_type = models.CharField(max_length=10)

    # 제시된 상징들 (JSON 형태로 저장)
    presented_symbols = models.JSONField()

    # 응답 데이터
    selected_symbol = models.CharField(max_length=50)
    is_correct = models.BooleanField()
    reaction_time = models.IntegerField()
    error_count = models.IntegerField(default=0)

    # 메타 데이터
    responded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trial_responses'
        ordering = ['participant', 'trial_number']
        indexes = [
            models.Index(fields=['participant', 'trial_number']),
            models.Index(fields=['symbol_type']),
        ]

    def __str__(self):
        return f"{self.participant.participant_id} - Trial {self.trial_number}"


class SymbolPreference(models.Model):
    """단어별 상징 선호도 (7개 단어)"""
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='symbol_preferences'
    )

    # 대상 단어
    target_word = models.CharField(max_length=20, verbose_name="대상 단어")

    # AI 상징 위치 (왼쪽/오른쪽)
    ai_position = models.CharField(max_length=10, choices=[
        ('left', '왼쪽'),
        ('right', '오른쪽')
    ], verbose_name="AI 위치")

    # 선택한 옵션
    chosen = models.CharField(max_length=10, choices=[
        ('left', '왼쪽'),
        ('right', '오른쪽'),
        ('similar', '비슷하다')
    ], verbose_name="선택")

    # 선택한 유형 (실제 선택된 상징 타입)
    chosen_type = models.CharField(max_length=10, choices=[
        ('ai', 'AI 상징'),
        ('kaac', 'KAAC 상징'),
        ('similar', '비슷하다')
    ], verbose_name="선택 유형")

    # 메타 데이터
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'symbol_preferences'
        ordering = ['participant', 'target_word']
        # 참가자당 각 단어에 대해 1개씩만
        unique_together = ['participant', 'target_word']
        indexes = [
            models.Index(fields=['participant', 'target_word']),
            models.Index(fields=['chosen_type']),
        ]

    def __str__(self):
        return f"{self.participant.participant_id} - {self.target_word}: {self.chosen_type}"


class Preference(models.Model):
    """전체 선호도 조사 데이터 (legacy - 사용 안 함)"""
    participant = models.OneToOneField(Participant, on_delete=models.CASCADE, related_name='preference')

    # 질문 1: 어떤 상징이 더 이해하기 쉬웠나요?
    easier_to_understand = models.CharField(max_length=10, choices=[
        ('ai', 'AI 생성 상징'),
        ('kaac', 'KAAC 상징'),
        ('similar', '비슷함')
    ])

    # 질문 2: 어떤 상징을 더 선호하나요?
    preference = models.CharField(max_length=10, choices=[
        ('ai', 'AI 생성 상징'),
        ('kaac', 'KAAC 상징'),
        ('similar', '비슷함')
    ])

    # 질문 3: 이유 (자유 응답)
    reason = models.TextField(blank=True)

    # 메타 데이터
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'preferences'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.participant.participant_id} - Preference"