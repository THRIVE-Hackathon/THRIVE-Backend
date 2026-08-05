# THRIVE Backend

> 장거리 비행 후, 회복이 끝나기 전에 다음 일정이 시작되는 사람들을 위한 회복 관리 서비스

THRIVE는 비행 조건과 회복 기록을 바탕으로 사용자의 회복 상태를 점수화하고, 다음 일정 전까지 수행할 회복 계획을 제공하는 Django 기반 백엔드입니다.

현재 저장소는 해커톤 MVP를 목표로 하며, 인증/프로필/여정/회복/리포트 도메인을 분리해 개발합니다.

## Tech Stack

| Layer | Stack |
| --- | --- |
| Language | Python 3.11+ |
| Framework | Django 5.0.x |
| Database | SQLite for local MVP |
| Config | django-environ |
| Template | Django Templates |
| Test | Django TestCase |

## Core Domain

```text
User
 └─ Profile
 └─ Trip
     ├─ InflightCheck
     ├─ RecoveryItem
     ├─ DailyCondition
     └─ TripResult
```

### Trip Lifecycle

```text
created -> landed -> recovering -> done
```

| Status | Meaning |
| --- | --- |
| `created` | 여정 등록 완료, 착륙 전 |
| `landed` | 착륙 확인 완료 |
| `recovering` | 실측 점수와 회복 계획 생성 완료 |
| `done` | 다음 일정 이후, 리포트 작성 대상 |

진행 중 여정은 사용자당 최대 1개만 허용합니다.

## App Architecture

```text
THRIVE/
├── config/              # Django project settings
├── accounts/            # User, Profile, auth, settings
├── trips/               # Trip, City, journey list, calendar export
├── recovery/            # RecoveryItem, DailyCondition, InflightCheck
├── reports/             # TripResult, recovery report
├── common/
│   └── services/        # calendar, score, timezone services
├── templates/           # Server-rendered pages
├── static/              # CSS / JS
└── docs/                # Backend planning documents
```

## Implemented Features

### Backend A

- Login / logout
- Signup with email uniqueness check
- Password hashing
- Profile setup, profile view, profile edit
- Settings page
- Account deletion
- Trip list
- Recovery report
- Disruption score submission
- `.ics` calendar export
- Basic templates and CSS
- Backend planning docs

### Shared Foundation

- Custom email-based `User`
- `Profile`, `City`, `Trip`, `RecoveryItem`, `DailyCondition`, `InflightCheck`, `TripResult` models
- Admin registration
- Initial migrations
- Common calendar, score, timezone service modules
- Tests for auth/profile/report/trip list/calendar

## Local Setup

### 1. Clone

```bash
git clone https://github.com/choiha522-wq/THRIVE.git
cd THRIVE
```

### 2. Create Virtual Environment

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create `.env` from `.env.example`.

```bash
cp .env.example .env
```

Example:

```env
SECRET_KEY=your-local-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
AI_API_KEY=
```

`.env` must never be committed.

### 5. Migrate

```bash
python manage.py migrate
```

### 6. Run Server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/accounts/login/
```

## Quality Checks

```bash
python manage.py check
python manage.py test
```

Current baseline:

```text
8 tests passing
```

## Main Routes

| Route | Name | Description |
| --- | --- | --- |
| `/accounts/login/` | `accounts:login` | 로그인 |
| `/accounts/signup/` | `accounts:signup` | 회원가입 |
| `/accounts/profile/setup/` | `accounts:profile_setup` | 최초 프로필 입력 |
| `/accounts/profile/` | `accounts:profile` | 프로필 조회 |
| `/accounts/profile/edit/` | `accounts:profile_edit` | 프로필 수정 |
| `/accounts/settings/` | `accounts:settings` | 설정 |
| `/trips/` | `trips:list` | 여정 목록 |
| `/trips/<trip_id>/calendar.ics` | `trips:calendar` | 캘린더 다운로드 |
| `/reports/<trip_id>/` | `reports:detail` | 회복 리포트 |

## Backend Ownership

| Owner | Scope |
| --- | --- |
| Backend A | 로그인, 회원가입, 프로필, 설정, 회복 리포트, 여정 목록, 캘린더 |
| Backend B | 여정 등록, 예상 점수, 실측 점수, 회복 계획, 체크 기록, 레이오버, AI 기능, 점수 계산 |

## Development Rules

- Feature work should be committed in small, reviewable units.
- Do not commit `.env`, `.venv`, `db.sqlite3`, or cache files.
- Model changes must include migrations.
- Store datetime values in UTC.
- Convert display times using the destination city timezone.
- Keep score logic inside `common/services/score.py`.
- Keep timezone logic inside `common/services/timezone.py`.
- Keep calendar export logic inside `common/services/calendar.py`.

## Documentation

| Document | Description |
| --- | --- |
| [`docs/backend-project-overview.md`](docs/backend-project-overview.md) | 프로젝트 전반과 백엔드 도메인 이해 |
| [`docs/backend-common-agreements.md`](docs/backend-common-agreements.md) | 백엔드 공통 협의, 앱 구조, Git 규칙 |

## Project Principle

THRIVE does not provide medical diagnosis or treatment.

Recovery scores are reference indicators for wellness guidance. The service intentionally avoids collecting sensitive medical data such as underlying diseases, diagnoses, and prescriptions during the MVP phase.
