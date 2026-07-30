# Hermes News Automation Skill 배포 가이드

> 기준일: 2026-07-29
>
> 상태: v0.1.0 공개 배포 · skills.sh 인덱싱·설치 검증 완료 · Hermes 0.19.0 custom tap 검색 제약 확인
>
> 배포 단위: `skills/hermes-news-automation/`

이 문서는 `hermes-news-automation`을 동료와 외부 사용자가 repository runtime을
별도로 clone하지 않고 설치·초기화·업데이트하는 절차를 정의한다.

## 1. 배포 구조

```text
skills/hermes-news-automation/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── artifact-schema.md
└── scripts/
    ├── run.py
    ├── precheck.py
    └── runtime/
        └── hermes_agent/
```

- `SKILL.md`: agent trigger, workflow와 실패 조건
- `scripts/run.py`: workspace 초기화, 진단과 controller 실행
- `scripts/precheck.py`: 변경이 있을 때만 cron agent를 깨우는 deterministic gate
- `scripts/runtime/`: runtime dependency가 없는 Python controller
- `references/`: agent artifact 계약
- `agents/openai.yaml`: Codex host용 선택 metadata

Skill 폴더 밖의 `Automation/`, 프로젝트 문서와 Obsidian Vault는 설치 bundle의
runtime dependency가 아니다.

## 2. 지원 환경

| 환경 | 상태 | Python 명령 |
| --- | --- | --- |
| macOS | 지원 | `python3` |
| Linux | 지원 | `python3` |
| Windows WSL2 | 지원 | `python3` |
| native Windows | 실험 지원 | `python` |

Python 3.9 이상, Hermes의 `terminal`, `web`, `file`, `delegation` toolset과 local
persistent filesystem이 필요하다.

## 3. skills.sh identifier로 설치

Release tag가 만들어진 뒤 설치 전 내용을 확인한다.

```bash
hermes skills inspect \
  skills-sh/dumbbelloper/hermes-agent/skills/hermes-news-automation
```

설치:

```bash
hermes skills install \
  skills-sh/dumbbelloper/hermes-agent/skills/hermes-news-automation
```

Hermes는 설치 source와 bundle hash를 기록하고 community Skill 보안 검사를
수행한다. 경고를 검토하지 않고 `--force`를 사용하지 않는다.
[skills.sh 공개 상세 페이지](https://skills.sh/dumbbelloper/hermes-agent/skills/hermes-news-automation)에서
현재 인덱싱 상태를 확인할 수 있다.

## 4. Hermes Tap으로 구독

이 repository는 root `skills/`와 `skills.sh.json`을 포함하므로 Hermes tap으로
등록할 수 있다.

```bash
hermes skills tap add dumbbelloper/hermes-agent
hermes skills search hermes-news
hermes skills install \
  dumbbelloper/hermes-agent/hermes-news-automation
```

Hermes 0.19.0에서는 tap 등록과 `skills/` 경로 인식은 확인했지만, 등록 직후
`hermes skills search`가 이 repository의 결과를 반환하지 않았다. 공개 설치는
3절의 검증된 skills.sh identifier를 우선 사용하고, custom tap 검색·설치는
Hermes version별로 재검증한 뒤 사용한다.

조직 내부 private repository라면 사용자의 Hermes profile에 GitHub 접근 권한을
제공하되 token을 Skill이나 repository에 저장하지 않는다.

## 5. Workspace 초기화

설치된 Skill 위치를 확인한다.

```bash
hermes skills list
```

기본 Hermes profile의 macOS/Linux/WSL2 예:

```bash
export HERMES_NEWS_SKILL_DIR="$HOME/.hermes/skills/hermes-news-automation"
python3 "$HERMES_NEWS_SKILL_DIR/scripts/run.py" init \
  --workspace "$HOME/hermes-news-workspace"
```

Native Windows PowerShell 예:

```powershell
$env:HERMES_NEWS_SKILL_DIR = Join-Path `
  $env:LOCALAPPDATA "hermes\skills\hermes-news-automation"
python "$env:HERMES_NEWS_SKILL_DIR\scripts\run.py" init `
  --workspace "$env:USERPROFILE\hermes-news-workspace"
```

초기화 결과:

```text
<workspace>/
├── Inbox/
└── .hermes-news/
    ├── config/
    │   ├── sources.json
    │   └── telegram.json  # 사용자가 별도 생성
    ├── data/
    └── tmp/
```

기존 `sources.json`은 덮어쓰지 않는다. 각 사용자와 runner는 별도 workspace를
사용한다.

## 6. 환경변수와 Telegram credential

Hermes의 `hermes config env-path`가 가리키는 env 파일에 설정한다.

```dotenv
HERMES_NEWS_WORKSPACE=<absolute-workspace-path>
HERMES_NEWS_SKILL_DIR=<absolute-installed-skill-path>
HERMES_NEWS_MAX_ITEMS=5
```

Telegram Bot credential은
`<workspace>/.hermes-news/config/telegram.json`에 다음 JSON object로 저장한다.

```json
{
  "bot_token": "<secret>",
  "chat_id": "<fixed-recipient>"
}
```

이 파일을 Git에 추가하지 않는다. macOS/Linux/WSL2에서는 `chmod 600`으로
소유자만 읽게 하고 native Windows에서는 현재 사용자와 cron runner만 읽도록 ACL을
제한한다. 기존 `HERMES_TELEGRAM_BOT_TOKEN`, `HERMES_TELEGRAM_CHAT_ID` 환경변수는
`v0.1.0`부터 runtime이 읽지 않는다.

설정 진단:

```bash
python3 "$HERMES_NEWS_SKILL_DIR/scripts/run.py" doctor \
  --workspace "$HERMES_NEWS_WORKSPACE"
```

`doctor`는 credential 값은 출력하지 않고 설정 여부만 반환한다.

## 7. Cron pre-check 설치

macOS/Linux/WSL2:

```bash
mkdir -p ~/.hermes/scripts
cp "$HERMES_NEWS_SKILL_DIR/scripts/precheck.py" \
  ~/.hermes/scripts/hermes-news-precheck.py
chmod 700 ~/.hermes/scripts/hermes-news-precheck.py
```

Native Windows PowerShell:

```powershell
$HermesScripts = Join-Path $env:LOCALAPPDATA "hermes\scripts"
New-Item -ItemType Directory -Force $HermesScripts | Out-Null
Copy-Item `
  "$env:HERMES_NEWS_SKILL_DIR\scripts\precheck.py" `
  "$HermesScripts\hermes-news-precheck.py" `
  -Force
```

Cron 생성과 gateway 운영은 [Hermes Agent 무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)를
따른다.

## 8. 업데이트와 제거

업스트림 변경 확인:

```bash
hermes skills check
```

Skill 업데이트:

```bash
hermes skills update hermes-news-automation
```

업데이트 후 pre-check를 다시 복사하고 `doctor`, registry validation과 cron
smoke test를 실행한다.

```bash
python3 "$HERMES_NEWS_SKILL_DIR/scripts/run.py" doctor
python3 "$HERMES_NEWS_SKILL_DIR/scripts/run.py" validate-registry
```

제거:

```bash
hermes skills uninstall hermes-news-automation
```

제거는 사용자의 workspace와 `.hermes-news/data/`를 자동 삭제하지 않는다.

## 9. 다른 Agent에 설치

Agent Skills 호환 installer를 사용할 수 있다.

```bash
npx skills add dumbbelloper/hermes-agent \
  --skill hermes-news-automation
```

설치 형식은 호환되지만 전체 workflow에는 Hermes cron, web extraction과 delegation
계약이 필요하다. 다른 host에서는 Skill 발견까지만 호환될 수 있으며 기능 호환은
별도로 검증해야 한다.

## 10. Maintainer release gate

Release 전에 다음을 모두 통과한다.

1. Skill validator
2. 전체 offline unit/integration test
3. repository 밖으로 복사한 bundle의 `init → doctor → validate-registry`
4. macOS, Linux와 Windows CI
5. credential·개인 경로·실행 state 미포함 검사
6. `SKILL.md`의 모든 상대 링크가 bundle 내부에 존재하는지 검사
7. version tag와 release note 작성

초기 공개 version은 `v0.1.0`으로 시작한다. 호환되지 않는 artifact schema나
workspace 변경은 major version에서만 수행한다.
