# Number is Matter (numberismatter)

**성장형 주사위 배틀 로그라이트**. Django 풀스택 개인 프로젝트.

🎮 **라이브: http://13.209.94.98**

---

## 게임 소개

매 턴 주사위를 굴려 적과 싸우고, 스테이지를 진행하며 골드를 모아 영구 성장하는 로그라이트입니다.

- **3주사위 전투** — 매 턴 공격 / 수비 / 회복 주사위 3개를 굴려 **하나만** 골라 사용
- **적 인텐트** — 적의 다음 행동(공격 N피해 / 방어 태세)을 미리 표시 (Slay the Spire식)
- **방어구** — 적이 방어 시 한 턴짜리 방어구 획득(누적 X). 큰 공격으로 뚫어야 함
- **3막 × 4스테이지** — 자연(Act1) → 던전(Act2) → 지하(Act3), 각 막 마지막은 보스. 적 18종, 일부는 희귀 등장(전설의 바퀴벌레 3%)
- **상점 / 영구 업그레이드** — 귀환 시 적립한 골드로 최대 HP·주사위 상한·크리티컬·골드 보너스를 영구 강화
- **런 경제** — 클리어 보상은 임시 골드, **귀환해야 영구 적립**. 사망하면 그 런의 보상은 소멸

## 기술 스택

| 분류 | 사용 |
|---|---|
| 백엔드 | Django 6, Python 3.12 |
| DB | PostgreSQL (로컬 runserver는 SQLite 폴백) |
| 프론트 | Django 템플릿 + **htmx**(전투 비동기화, 페이지 새로고침 없이 전투 영역만 교체) |
| 정적파일 | WhiteNoise |
| 배포 | Docker Compose (gunicorn + postgres), AWS EC2 |
| 도구 | uv(패키지/실행), ruff(린트·포맷), coverage(테스트 커버리지) |

## 아키텍처

```
URL (urls.py)  →  View (HTTP 처리: 세션·요청·응답·htmx)
                    └─ Service (services.py: 게임 규칙·전투 계산·상점 로직)
                         └─ ORM (Django Manager/QuerySet: 데이터 접근)
```

- 진행 중인 런(run) 상태는 **세션**에 저장 (모델이 아닌 dict). 영구 데이터(골드·업그레이드)만 DB.
- 비즈니스 로직은 `services.py`에 분리해 `request` 없이 단위 테스트 가능.

## 로컬 실행

[uv](https://docs.astral.sh/uv/)가 필요합니다.

```bash
# 1) 의존성 설치
uv sync

# 2) 환경변수 파일 생성 후 SECRET_KEY 채우기
cp .env.example .env
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
#   → 출력된 키를 .env의 SECRET_KEY에 붙여넣기 (DATABASE_URL 없으면 SQLite로 자동 실행)

# 3) DB 마이그레이션 (적·업그레이드 시드 포함)
uv run python manage.py migrate

# 4) 개발 서버
uv run python manage.py runserver
#   → http://127.0.0.1:8000
```

## 테스트 / 커버리지

```bash
uv run python manage.py test          # 전체 테스트
uv run coverage run manage.py test    # 커버리지 측정하며 실행
uv run coverage report                # 표로 출력 (안 탄 줄 번호 포함)
uv run coverage html                  # htmlcov/index.html 상세 리포트
```

린트/포맷:
```bash
uv run ruff check .          # 검사
uv run ruff check . --fix    # 자동 수정
```

## 배포 (Docker)

비밀값은 서버의 `.env`(git 미포함)로 전달합니다.

```bash
docker compose up -d --build
docker compose exec web uv run python manage.py migrate
```

- `web`: gunicorn으로 Django 서빙 (80→8000), 빌드 시 `collectstatic` 자동
- `db`: postgres:16
- 코드/정적파일이 이미지에 빌드되므로 업데이트 시 `--build` 필요

## 프로젝트 구조

```
numberismatter/      # 프로젝트 설정 (settings, urls, wsgi/asgi)
accounts/            # 커스텀 유저(이메일/닉네임), 로그인·회원가입·비번변경
game/                # 게임 코어
  ├─ models.py       #   Character, Enemy, Upgrade, CharacterUpgrade, Skill
  ├─ views.py        #   HTTP 레이어 (전투·상점·런 진행)
  ├─ services.py     #   게임 로직 (상점·비용 계산 등)
  ├─ migrations/     #   스키마 + 적/업그레이드 시드 데이터
  ├─ static/game/    #   몬스터 이미지, htmx.min.js
  └─ tests/
templates/           # base.html(스타일 포함) + game·account 화면
```
