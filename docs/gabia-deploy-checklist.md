# 가비아 클라우드 Django 배포 체크리스트

대상: THRIVE 백엔드 Django 서버

## 지원 서버 조건

- 제공사: 가비아 클라우드
- 사용 기간: 8/18(화) ~ 8/28(금), 10일 간
- 서버 개수: 팀당 1개
- 서버 타입: High CPU
- CPU: 2vCore
- 메모리: 4GB
- 무료 트래픽: 1TB
- 공인 IP: 1개
- 스토리지: 아래 중 택 1
  - 루트 스토리지 100GB
  - 루트 스토리지 50GB + 데이터 스토리지 50GB

## 과금 주의

- 제공 사양보다 높은 사양을 선택하면 비용이 발생할 수 있다.
- 추가 서비스를 선택하면 연결된 결제 수단으로 비용이 발생할 수 있다.
- 관리 콘솔에 보이는 정상 과금 금액은 추후 제공 사양 범위 내에서 0원 처리 예정.
- 8/28(금) 23:59 서버가 일괄 삭제되므로 제출 이후 필요한 데이터는 미리 백업해야 한다.

## 기술 지원

- 기술 지원 기간: 8/18(화) ~ 8/21(금) 18:00
- 문의처: gajet@gabia.com
- 메일 제목 예시:

```text
[ID : likelion] LANDING_서버명 기술지원 문의드립니다.
```

## 팀장에게 받아야 할 정보

- 공인 IP
- 서버 OS와 버전
- SSH 접속 계정
- SSH 비밀번호 또는 private key 파일
- 도메인 연결 여부
- 가비아 방화벽/보안그룹에서 열려 있는 포트

## 서버 기본 준비

Ubuntu 기준 예시:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx
```

## 프로젝트 배포

```bash
git clone https://github.com/THRIVE-Hackathon/THRIVE-Backend.git
cd THRIVE-Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 환경변수

서버에는 `.env` 파일을 직접 생성한다. 이 파일은 GitHub에 올리지 않는다.

```env
SECRET_KEY=운영용_랜덤_SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=공인IP,도메인
CSRF_TRUSTED_ORIGINS=http://공인IP,https://도메인
AI_API_KEY=Gemini_API_KEY
```

도메인을 연결하지 않고 공인 IP만 사용할 경우:

```env
ALLOWED_HOSTS=서버_공인_IP
CSRF_TRUSTED_ORIGINS=http://서버_공인_IP
```

## 초기화

```bash
python manage.py migrate
python manage.py seed_airports
python manage.py collectstatic --no-input
python manage.py check
```

## Gunicorn 실행 확인

```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

서버 안에서 확인:

```bash
curl http://127.0.0.1:8000/accounts/login/
```

## systemd 서비스 예시

`/etc/systemd/system/thrive.service`

```ini
[Unit]
Description=THRIVE Django Gunicorn
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/THRIVE-Backend
EnvironmentFile=/home/ubuntu/THRIVE-Backend/.env
ExecStart=/home/ubuntu/THRIVE-Backend/.venv/bin/gunicorn config.wsgi:application --workers 3 --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

적용:

```bash
sudo systemctl daemon-reload
sudo systemctl enable thrive
sudo systemctl start thrive
sudo systemctl status thrive
```

## Nginx 예시

`/etc/nginx/sites-available/thrive`

```nginx
server {
    listen 80;
    server_name 서버_공인_IP 또는 도메인;

    location /static/ {
        alias /home/ubuntu/THRIVE-Backend/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

적용:

```bash
sudo ln -s /etc/nginx/sites-available/thrive /etc/nginx/sites-enabled/thrive
sudo nginx -t
sudo systemctl restart nginx
```

## 배포 후 확인

- `http://공인IP/accounts/login/` 접속
- 회원가입 -> 프로필 설정 이동 확인
- 로그인 확인
- 여정 등록 확인
- 비행 전 예상 점수 화면 확인
- 회복 가이드 확인
- 비행 중 체크리스트 확인
- 착륙 점수 확인
- 회복 루틴 확인

## 제출 문서 기입

```md
배포 완료 프로덕트 URL:
http://공인IP/

테스트 계정:
이메일:
비밀번호:
```

도메인을 연결한 경우 공인 IP 대신 도메인 URL을 제출한다.

## 제출 전 백업

서버는 8/28(금) 23:59에 삭제 예정이므로, 제출 이후에도 보존해야 하는 데이터는 로컬로 내려받는다.

SQLite를 사용하는 경우:

```bash
cp db.sqlite3 db.sqlite3.backup
```

PostgreSQL을 사용하는 경우:

```bash
pg_dump 데이터베이스명 > thrive_backup.sql
```
