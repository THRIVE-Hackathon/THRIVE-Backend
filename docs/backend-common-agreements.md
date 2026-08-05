# 백엔드 공통 협의 및 공동 구현

작성일: 2026-08-06  
원문: `KakaoTalk_Longtxt_20260806_0430_22_539.txt`  
목적: 백엔드 팀원이 같은 구조, 같은 명명 규칙, 같은 상태/점수/시간 처리 기준으로 개발하기 위한 공통 합의사항을 정리한다.

## 1. 가장 먼저 같이 해야 할 것

아래 항목은 각자 기능 구현을 시작하기 전에 먼저 맞춰야 한다.

1. Django 프로젝트명과 앱 구조 확정
2. 공통 `settings.py`, `urls.py`, `templates/`, `static/` 구조 생성
3. 환경변수와 `.env.example` 관리 방식 확정
4. `User`, `Profile`, `City`, `Trip` 중심의 1차 모델 정의
5. Trip 상태값과 상태 전이 조건 확정
6. 시간대 처리 기준 확정
7. 점수 계산 로직의 1차 상수와 함수 위치 확정
8. Git 브랜치, PR, migration 작업 규칙 확정

## 1-1. 백엔드 역할 분담

| 담당 | 이름 | 범위 |
| --- | --- | --- |
| 백엔드 A | 최유정 | 로그인, 회원가입, 프로필, 설정, 회복 리포트, 여정 목록, 캘린더 |
| 백엔드 B | 최현아 | 여정 등록, 예상 점수, 실측 점수, 회복 계획, 체크 기록, 레이오버, AI 기능, 점수 계산 |

현재 구현은 백엔드 A 범위를 먼저 진행한다. 다만 A 화면이 동작하려면 Trip, City, RecoveryItem, TripResult 같은 공통 모델이 필요하므로, 모델과 공통 서비스의 최소 뼈대는 함께 생성한다.

## 2. 프로젝트 구조

프로젝트명은 팀명 기준으로 `THRIVE` 또는 Django 내부 명칭 `thrive`를 사용한다. `LANDING`은 아직 가칭이므로 서비스명 변경 가능성을 고려해 Django 프로젝트명으로 고정하지 않는 편이 좋다.

권장 구조:

```text
thrive/
├── config/
├── accounts/
├── trips/
├── recovery/
├── reports/
├── common/
│   ├── ai/
│   └── services/
├── templates/
└── static/
```

앱 분리 기준:

| 앱 | 책임 |
| --- | --- |
| `accounts` | User, Profile, 인증, 프로필 |
| `trips` | Trip, City, 여정 등록, 여정 상태, 점수 |
| `recovery` | RecoveryItem, DailyCondition, InflightCheck |
| `reports` | TripResult, 리포트, 비교 |
| `common` | AI 호출, 점수 계산, 시간대 처리 등 공통 서비스 |

## 3. Templates와 Static

공통 템플릿은 루트 `templates/`에 둔다.

```text
templates/
├── base.html
├── accounts/
├── trips/
├── recovery/
└── reports/
```

정적 파일은 루트 `static/`에 둔다.

```text
static/
├── css/
└── js/
```

템플릿 파일명은 URL name과 최대한 대응되게 만든다.

예:

| URL name | Template |
| --- | --- |
| `trips:create` | `trips/create.html` |
| `trips:expected_score` | `trips/expected_score.html` |
| `recovery:plan` | `recovery/plan.html` |

## 4. 환경변수와 패키지 관리

환경변수는 `django-environ` 사용을 권장한다.

```bash
pip install django-environ
```

`.env`는 커밋하지 않고 `.gitignore`에 추가한다. 대신 `.env.example`은 커밋해서 팀원이 필요한 키를 알 수 있게 한다.

`.env.example` 예시:

```env
SECRET_KEY=
DEBUG=
AI_API_KEY=
```

`settings.py` 예시:

```python
import environ

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
AI_API_KEY = env("AI_API_KEY", default="")
```

Python과 Django 버전:

| 항목 | 권장 |
| --- | --- |
| Python | 3.11 이상 |
| Django | `>=5.0,<5.1` |

패키지 설치 후에는 바로 `requirements.txt`를 갱신한다.

```bash
pip freeze > requirements.txt
pip install -r requirements.txt
```

## 5. 모델 관계

핵심 관계:

| 관계 | 설명 |
| --- | --- |
| User - Profile | 1:1. 회원가입 직후에는 Profile이 없고, A3 완료 시 생성 |
| User - Trip | 1:N. 단, 진행 중 Trip은 사용자당 최대 1개 |
| Trip - City | Trip 하나가 City를 출발지/도착지로 각각 참조 |
| Trip - InflightCheck | 1:N |
| Trip - RecoveryItem | 1:N |
| Trip - DailyCondition | 1:N |
| Trip - TripResult | 1:1. 여정 결과 입력 시 생성 |

City를 두 번 참조하므로 `related_name`을 분리해야 한다.

예:

```python
origin_city = models.ForeignKey(
    City,
    on_delete=models.PROTECT,
    related_name="origin_trips",
)
destination_city = models.ForeignKey(
    City,
    on_delete=models.PROTECT,
    related_name="destination_trips",
)
```

## 6. 필드명 규칙

### 시간 필드

시간 관련 필드는 `_at`으로 끝낸다.

좋은 예:

- `created_at`
- `updated_at`
- `landed_at`
- `scheduled_at`
- `completed_at`

피할 예:

- `landing_time`
- `landedAt`
- `complete_date`

### 점수 필드

점수는 역할이 드러나게 쓴다.

| 필드 | 의미 |
| --- | --- |
| `expected_score` | 비행 전 예상 회복 점수 |
| `actual_score` | 착륙 후 실측 회복 점수 |
| `current_score` | 회복 진행 중 현재 점수 |
| `target_score` | 다음 일정 전 목표 점수 |

단순히 `score`만 쓰면 화면마다 의미가 달라져 혼동될 수 있다.

### 상태 필드

상태값 필드는 `status`로 통일한다.

Trip 상태:

```text
created -> landed -> recovering -> done
```

## 7. 필수값, 선택값, 기본값

### DB에서도 필수로 둘 값

- User 이메일
- Profile 닉네임, 성별, 연령대
- Trip 출발지, 도착지, 총 비행시간, 다음 일정까지 시간

화면에서 입력하지 않으면 다음 버튼이 비활성화되는 값은 DB에서도 기본적으로 필수로 본다.

### 조건부 필수

경유 대기시간은 경유가 없으면 비어도 된다. 경유가 1회 이상이면 필수다.

### 나중에 채워지는 선택값

아래 값은 처음 Trip 생성 시 비어 있을 수 있다.

- `expected_score`
- `actual_score`
- `target_score`
- `current_score`
- `landed_at`

이 값들은 "필수인데 나중에 채우는 값"이 아니라 "처음에는 비어 있다가 특정 상태에서 채워지는 값"으로 이해한다.

### 기본값

| 모델/필드 | 기본값 |
| --- | --- |
| Trip.status | `created` |
| Trip.layover_count | `none` 또는 0 |
| InflightCheck.count | 0 |
| RecoveryItem.status | `pending` |

## 8. 삭제 방식

기본 방향:

| 데이터 | 삭제 방식 |
| --- | --- |
| User | 하드 삭제 또는 정책에 따른 전체 삭제 |
| Trip | 삭제 시 하위 데이터 함께 삭제 |
| InflightCheck | Trip 삭제 시 함께 삭제 |
| RecoveryItem | Trip 삭제 시 함께 삭제 |
| DailyCondition | Trip 삭제 시 함께 삭제 |
| TripResult | Trip 삭제 시 함께 삭제 |
| City | 삭제 기능을 만들지 않음 |

City는 여러 Trip이 참조할 수 있는 고정 데이터이므로 삭제하지 않는다. 모델에서는 `on_delete=PROTECT`가 적합하다.

## 9. 공통 timestamp 규칙

`created_at`은 모든 주요 모델에 둔다.

`updated_at`은 실제로 자주 수정되는 모델에 둔다.

우선 권장:

| 모델 | created_at | updated_at |
| --- | --- | --- |
| User | 필요 | 필요 |
| Profile | 필요 | 필요 |
| Trip | 필요 | 필요 |
| RecoveryItem | 필요 | 필요 |
| DailyCondition | 필요 | 선택 |
| InflightCheck | 필요 | 필요 |
| TripResult | 필요 | 선택 |
| City | 필요 | 선택 |

## 10. 여정 상태값

### 상태 정의

| 상태 | 의미 |
| --- | --- |
| `created` | S1 여정 등록 완료 후 최초 상태 |
| `landed` | 예정 착륙 시각이 지났고 사용자가 착륙 확인을 완료한 상태 |
| `recovering` | 실측 점수 계산과 회복 항목 생성이 끝난 상태 |
| `done` | 다음 일정 시각이 지난 상태 |

### 상태 전이

| 전이 | 방식 | 조건 |
| --- | --- | --- |
| `created -> landed` | 자동 감지 + 사용자 확인 | 예정 착륙 시각 경과 후 사용자가 착륙 확인 |
| `landed -> recovering` | 자동 | 실측 점수 계산과 RecoveryItem 생성 완료 |
| `recovering -> done` | 자동 | 다음 일정 시각 경과 |

### 상태별 홈 화면

| 상태 | 홈 탭 화면 |
| --- | --- |
| 진행 중 여정 없음 | S1 여정 등록 |
| `created` | S2 예상 회복 점수 |
| `landed` | S4 실측 회복 점수 |
| `recovering` | S5 회복 계획 |
| `done` | S5 유지 + 리포트 안내 배너 |

### 진행 중 여정 기준

아래 상태는 모두 진행 중 여정이다.

- `created`
- `landed`
- `recovering`

계정당 진행 중 여정은 최대 1개로 제한한다.

### 완료된 여정 기준

`done` 상태이면서 `TripResult`까지 입력된 경우를 완료된 여정으로 본다.

`done`이지만 `TripResult`가 없으면 S9 여정 목록에서 `리포트 작성 필요`로 표시한다.

## 11. 점수 계산 로직

### 예상 점수

기본 100점에서 감점 요소를 빼는 방식으로 시작한다.

주요 감점 요소:

- 시차 시간
- 총 비행시간
- 경유 횟수
- 동행/서행 여부

동행은 서행보다 적응이 어렵다는 전제로 더 큰 감점을 줄 수 있다. 정확한 가중치는 테스트 시나리오를 기준으로 팀원과 함께 확정해야 한다.

기준 시나리오:

```text
인천 -> 파리
비행시간 13시간
시차 8시간
예상 점수 44점
```

### 요소별 감점

전체 감점은 네 요소에 나눠 배분한다.

| 요소 | 기준 |
| --- | --- |
| 수면 | 시차 영향을 가장 크게 받음 |
| 순환 | 총 비행시간과 부동 시간에 비례 |
| 수분 | 총 비행시간과 기내 건조 노출에 비례 |
| 피부 | 총 비행시간과 기내 습도 영향에 비례, 비교적 완만하게 감점 |

각 요소에는 감점 상한/하한을 둬 한 요소가 과도하게 깎이지 않도록 한다.

### 기내 기록 반영

InflightCheck가 있으면 해당 카테고리 감점을 일부 상쇄한다.

예:

| 기록 | 반영 |
| --- | --- |
| 물 마심 1회 | 수분 감점 일부 상쇄 |
| 걷기/스트레칭 | 순환 감점 일부 상쇄 |
| 보습 | 피부 감점 일부 상쇄 |

기내 기록이 없으면 예상 점수를 실측 점수로 그대로 사용한다.

### 목표 점수

다음 일정까지 남은 시간에 따라 회복 가능한 최대치를 계산한다.

- 남은 시간이 짧으면 보수적인 목표
- 남은 시간이 길면 100에 가까운 목표
- 100 초과 시 100으로 절사

### 회복 항목별 상승 점수

항목과 상승 점수 매핑표를 별도로 둔다.

예시:

| 항목 | 요소 | 상승 점수 |
| --- | --- | --- |
| 10분 걷기 | 순환 | +4 |
| 물 500ml | 수분 | +3 |
| 보습 | 피부 | +3 |
| 광 노출 30분 | 수면 | +5 |

### 하루 최대 회복 한도

하루에 오를 수 있는 점수 상한을 둔다.

예:

```text
하루 총 +15 상한
```

한도 초과 시:

- 체크 기록은 저장한다.
- 점수는 반영하지 않는다.
- 화면에는 "오늘은 충분히 하셨어요" 안내를 보여준다.

### 점수 범위와 반올림

- 모든 점수는 0~100 범위로 고정한다.
- 0 미만은 0, 100 초과는 100으로 절사한다.
- 화면에는 소수점 없는 정수로 보여준다.
- 반올림을 기본 권장한다.

## 12. 시간대 및 날짜 처리

### 서버와 DB 기준

서버와 DB 저장은 UTC 기준으로 통일한다.

```python
TIME_ZONE = "UTC"
USE_TZ = True
```

모든 `DateTimeField`는 timezone-aware datetime으로 저장한다. naive datetime 저장은 피한다.

### 화면 표시

사용자에게 보여줄 때만 도착지 현지 시간으로 변환한다.

공통 함수 위치:

```text
common/services/timezone.py
```

### 시차 계산

City에는 timezone을 저장한다.

권장:

```text
Asia/Seoul
Europe/Paris
America/Los_Angeles
```

Python `zoneinfo`를 사용해 출발지와 도착지의 UTC offset 차이를 계산한다. 고정 숫자 offset만 비교하면 서머타임 대응이 어렵다.

### 동행/서행 판단

출발지 대비 도착지 시간이 더 빠르면 동행, 더 늦으면 서행으로 판단한다.

이 판단은 공통 함수 하나로 통일하고 아래 로직에서 재사용한다.

- 점수 계산
- 광 노출 시간대 배치
- 레이오버 가이드

### 착륙 여부 자동 판정

도착 예정 시각을 UTC로 저장하고, 현재 UTC 시각과 비교한다.

```text
landing_at <= now
```

조건을 만족하면 사용자에게 "착륙하셨나요?" 확인을 요청한다.

### 회복 일정 생성 기준

RecoveryItem은 도착지 현지 시간 기준으로 생성한다.

예:

- 수면 항목은 현지 22:00~07:00에만 배치
- 동행이면 광 노출 오전 배치
- 서행이면 광 노출 오후 배치

## 13. URL과 View 규칙

앱별 URL prefix는 앱 이름과 동일하게 맞춘다.

| 앱 | Prefix |
| --- | --- |
| accounts | `/accounts/` |
| trips | `/trips/` |
| recovery | `/recovery/` |
| reports | `/reports/` |

URL name은 `앱이름:동작명` 형식으로 통일한다.

예:

```text
accounts:login
accounts:signup
accounts:profile_setup
trips:create
trips:expected_score
trips:actual_score
trips:list
recovery:plan
recovery:check
reports:detail
```

View는 함수형 뷰(FBV)로 통일하는 것을 권장한다. 현재 규모에서는 팀원 간 코드 리뷰와 흐름 파악이 쉽다.

redirect는 문자열 경로가 아니라 URL name을 사용한다.

```python
return redirect("trips:expected_score", trip_id=trip.id)
```

## 14. 공통 Context 변수명

템플릿에서 같은 의미의 데이터는 같은 변수명을 사용한다.

| 변수명 | 의미 |
| --- | --- |
| `trip` | 현재 여정 객체 |
| `profile` | 로그인 사용자 프로필 |
| `score` | 화면에서 다루는 대표 점수 |
| `recovery_items` | 회복 항목 목록 |
| `is_target_reached` | 목표 점수 도달 여부 |
| `error_message` | 공통 에러 메시지 |

화면별로 `trip_score`, `currentTrip`, `items`처럼 이름이 갈라지지 않도록 한다.

## 15. Git 협업 규칙

### 브랜치

```text
main
develop
feature/accounts
feature/trips
feature/recovery
feature/reports
```

앱 단위로 feature 브랜치를 나누어 모델 구조와 브랜치 구조를 맞춘다.

### 커밋 메시지

태그 접두어를 사용한다.

예:

```text
feat: Trip 모델 추가
fix: 시차 계산 오류 수정
docs: README 업데이트
```

### Pull Request

- 기능 하나 단위로 PR을 만든다.
- 너무 큰 PR로 묶지 않는다.
- 점수 계산 로직처럼 핵심 로직은 반드시 리뷰 후 merge한다.
- `develop`에 직접 push하지 않는다.

### Migration

Model 변경 전에는 반드시 팀원에게 공유한다.

규칙:

- migration 파일을 동시에 만들지 않는다.
- 모델을 바꾼 사람이 `makemigrations`를 실행하고 커밋한다.
- 다른 사람은 pull 받은 뒤 이어서 작업한다.
- migration 충돌 시 먼저 push된 쪽을 기준으로 나중 작업자가 migration을 다시 만든다.
- 필요하면 `makemigrations --merge`를 사용한다.

### 공통 파일 충돌 방지

아래 파일은 수정 전 담당자를 먼저 정한다.

- `settings.py`
- 프로젝트 루트 `urls.py`
- 공통 `base.html`
- 공통 CSS/JS
- 공통 service 함수

## 16. 공동 구현 체크리스트

### 1단계: 프로젝트 뼈대

- [ ] Django 프로젝트 생성
- [ ] `accounts`, `trips`, `recovery`, `reports`, `common` 앱 생성
- [ ] 루트 `templates/`, `static/` 생성
- [ ] `django-environ` 적용
- [ ] `.env.example` 작성
- [ ] `.gitignore`에 `.env`, venv, DB 파일 등 추가
- [ ] `requirements.txt` 생성

### 2단계: 공통 모델

- [ ] User/Profile 설계
- [ ] City 설계 및 seed 방식 결정
- [ ] Trip 설계
- [ ] Trip 상태값 choices 정의
- [ ] `created_at`, `updated_at` 공통 규칙 적용
- [ ] 진행 중 여정 1개 제한 방식 결정

### 3단계: 공통 서비스

- [ ] `common/services/timezone.py` 생성
- [ ] 시차 계산 함수 작성
- [ ] 동행/서행 판단 함수 작성
- [ ] `common/services/score.py` 생성
- [ ] 예상 점수 계산 함수 작성
- [ ] 실측 점수 계산 함수 작성
- [ ] 목표 점수 계산 함수 작성

### 4단계: 상태 전이

- [ ] `created -> landed` 처리
- [ ] `landed -> recovering` 처리
- [ ] `recovering -> done` 처리
- [ ] 재접속 시 착륙 확인 필요 여부 판단
- [ ] done이지만 TripResult 없는 여정 표시 방식 구현

### 5단계: 협업 운영

- [ ] `develop` 브랜치 생성
- [ ] 앱별 feature 브랜치 생성
- [ ] PR 템플릿 작성 여부 결정
- [ ] migration 담당 규칙 공유
- [ ] 공통 파일 수정 담당자 정하기

## 17. 추가로 확정해야 할 질문

아래는 구현 전에 팀 내에서 한 번 더 확정해야 한다.

| 질문 | 이유 |
| --- | --- |
| Django 프로젝트 내부명을 `thrive`로 할지 `config`로 할지 | 구조 예시에 둘 다 가능성이 있음 |
| 기본 User를 쓸지 custom User를 쓸지 | 이메일 로그인 기준이면 초기에 결정해야 나중에 비용이 작음 |
| `done` 전환을 다음 일정 시각 경과로 할지 TripResult 입력 완료로 할지 | 원문은 done 시각 경과, 완료 여정은 done + TripResult로 구분 |
| 착륙 예정 시각을 S1에서 직접 받을지 계산할지 | 자동 라우팅과 다음 일정 계산에 필요 |
| 점수 가중치의 실제 숫자 | 파리 13h/시차 8h = 44점 기준 역산 필요 |
| 하루 회복 한도를 총합으로 둘지 요소별로 둘지 | RecoveryItem 체크 로직에 영향 |
| City seed 범위 | 초기 지원 도시 목록 필요 |

## 18. 학습 메모

이 문서는 백엔드 구현의 공통 규칙으로 학습한다. 이후 코드 생성이나 설계 변경을 할 때 다음 기준을 우선 적용한다.

- Django 앱은 `accounts`, `trips`, `recovery`, `reports`, `common`으로 나눈다.
- 핵심 도메인은 Trip이며, 진행 중 Trip은 사용자당 최대 1개다.
- 시간은 DB에 UTC로 저장하고 화면/회복 일정은 도착지 현지 시간으로 변환한다.
- 점수 계산은 `common/services/score.py`, 시간대 처리는 `common/services/timezone.py`로 모은다.
- AI보다 재현 가능한 계산 로직과 상태 전이를 먼저 안정화한다.
- migration과 공통 파일은 팀원과 충돌하지 않게 작업 순서를 먼저 맞춘다.
