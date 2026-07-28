# Hermes Agent 무인 자동화 가이드

> 기준일: 2026-07-28
>
> 상태: v0.1.0 배포 완료 · 최초 실환경 cron 검증 필요
>
> 대상: macOS, Linux, Windows WSL2, native Windows

이 문서는 [Hermes News Automation Skill](./skills/hermes-news-automation/SKILL.md)을
Hermes Agent의 gateway와 cron으로 계속 실행하는 공통 운영 기준이다. 특정 Mac 경로나
`launchd`만을 전제로 하지 않으며, Agent Skills 공개 규격과 여러 agent 생태계에서
채택도가 높은 공개 구현의 공통 관행을 따른다.

## 1. 결론

- Skill의 이식성 기준은 OS 개수가 아니라 표준 `SKILL.md`, 상대 경로, 명시적 의존성,
  결정론적 script와 검증 가능한 실패 조건이다.
- macOS와 Linux를 1차 운영 환경으로 지원한다.
- Windows에서는 WSL2를 1차 운영 경로로 지원한다.
- native Windows는 Hermes 자체가 gateway와 cron을 지원하지만, 이 프로젝트의
  실환경 end-to-end 검증 전까지 실험 지원으로 분류한다.
- Skill은 운영 설명서가 아니다. 짧은 실행 절차만 Skill에 두고 설치·서비스·전원·복구
  절차는 이 문서에서 관리한다.

## 2. 참고한 규격과 공개 사례

아래 수치는 GitHub star를 채택 신호로만 사용한 2026-07-28 스냅샷이다. 저장소의
목적과 생성 시점이 달라 절대적인 품질 순위로 해석하지 않는다.

| 기준 또는 저장소 | 당시 공개 신호 | 채택한 관행 |
| --- | ---: | --- |
| [Agent Skills Specification](https://agentskills.io/specification) | 공개 표준 | `SKILL.md` 필수, `scripts/`·`references/`·`assets/` 선택, 점진적 정보 공개, 상대 링크, validator |
| [obra/superpowers](https://github.com/obra/superpowers) | 약 262k stars | 명령형 workflow, hard gate, 완료 전 검증, 여러 agent host별 얇은 adapter |
| [Anthropic Skills](https://github.com/anthropics/skills) | 약 151k stars | self-contained skill directory, 간결한 metadata, 복잡한 작업을 script와 reference로 분리 |
| [GitHub Awesome Copilot](https://github.com/github/awesome-copilot) | 약 37k stars | Agent Skills 규격 호환, 반복 workflow와 bundled resource 중심 구성 |
| [Vercel Labs Skills CLI](https://github.com/vercel-labs/skills) | 약 27k stars | 여러 agent 설치 경로 지원, project/global scope 분리, symlink 기반 single source of truth |
| [OpenAI Skills](https://github.com/openai/skills) | 약 24k stars | `agents/openai.yaml` host extension. 현재 저장소는 deprecated이므로 새 배포 기준으로 사용하지 않음 |

이 프로젝트가 적용하는 공통 규칙은 다음과 같다.

1. 디렉터리명과 `name`은 소문자 kebab-case로 일치시킨다.
2. frontmatter의 코어는 `name`과 “무엇을 하며 언제 쓰는지”를 함께 적은
   `description`으로 제한한다.
3. `SKILL.md`에는 agent가 반드시 따라야 하는 절차와 실패 조건만 둔다.
4. schema와 상세 지식은 `references/`, 반복되거나 취약한 동작은 `scripts/`에 둔다.
5. 연결된 파일은 Skill root 기준 상대 링크로 직접 참조하고 깊은 reference chain을
   만들지 않는다.
6. host 전용 metadata는 `agents/` 같은 확장 디렉터리로 격리한다.
7. inline 환경변수와 OS별 import 경로 조립 대신 Python launcher를 사용한다.
8. 실제 지원하지 않는 OS나 tool을 보편 지원한다고 표시하지 않는다.
9. 정적 validator, script 실행, 실패 경로와 end-to-end 표본을 구분해 검증한다.

현재 Skill 구조는 이 기준과 일치한다.

```text
skills/hermes-news-automation/
├── SKILL.md
├── LICENSE.txt
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

`agents/openai.yaml`은 Agent Skills 코어가 아니라 Codex UI용 확장이다. Hermes는 이를
필수로 요구하지 않으며, 다른 agent host도 `SKILL.md`와 직접 연결된 resource만으로
workflow를 이해할 수 있어야 한다.

## 3. 플랫폼 지원 정책

| 환경 | 등급 | gateway | lock backend | 운영 조건 |
| --- | --- | --- | --- | --- |
| macOS | 1차 지원 | `launchd` | Python 표준 라이브러리, `fcntl` lock | Mac이 켜져 있고 잠자지 않아야 함 |
| Linux | 1차 지원 | `systemd` user 또는 system service | Python 표준 라이브러리, `fcntl` lock | local persistent filesystem 권장 |
| Windows + WSL2 | 1차 지원 | WSL의 `systemd` | Linux와 동일 | WSL instance와 systemd가 계속 실행되어야 함 |
| native Windows 10/11 | 실험 지원 | Windows Scheduled Task | Python 표준 라이브러리, `msvcrt` lock | 이 프로젝트의 Windows E2E 검증 전 운영 승격 금지 |

Agent Skills 표준은 Windows 지원을 의무화하지 않는다. Hermes 공식
[native Windows 가이드](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/windows-native.md)는
CLI, gateway와 cron을 지원하며 terminal 명령은 Git Bash로 실행한다고 설명한다.
이 프로젝트도 POSIX 전용 inline 환경변수 대신 Skill bundle의 `scripts/run.py`를
공통 controller entrypoint로 사용한다. interpreter 명령만 POSIX에서는 `python3`,
native Windows에서는 `python`을 사용한다.

NFS, SMB, 동기화 드라이브를 `.hermes-news/data/`의 실행 저장소로 사용하지 않는다.
운영 상태의 file lock과 atomic replace 의미가 local filesystem과 다를 수 있기
때문이다. Obsidian 동기화가 필요하면 실행 중인 저장소는 local disk에 두고 별도
동기화 계층을 사용한다.

## 4. 공통 전제 조건

- Python 3.9 이상
- Git
- Hermes Agent와 사용 가능한 model provider
- local persistent workspace
- Telegram Bot token과 고정 chat ID
- cron agent에 `skills`, `terminal`, `file`, `web`, `delegation` toolset

확인:

```bash
python3 --version
hermes --version
hermes model
```

macOS/Linux/WSL2는 `python3`, native Windows PowerShell과 Git Bash는 `python`으로
확인한다. 둘 다 Python 3.9 이상이어야 하며, Skill은 이 interpreter로
설치 bundle의 `scripts/run.py`를 실행한다.

## 5. Workspace와 환경변수

초기화한 workspace는 OS별 임의의 local 절대 경로에 둘 수 있다.

```text
macOS 예:       /Users/<user>/hermes-news-workspace
Linux 예:       /srv/hermes-news-workspace
Windows WSL2:   /home/<user>/hermes-news-workspace
native Windows: C:\Users\<user>\hermes-news-workspace
```

설치와 초기화는 [Skill 배포 가이드](./SKILL_DISTRIBUTION_GUIDE.md)를 먼저 따른다.
`HERMES_NEWS_WORKSPACE`에는 workspace의 절대 경로를 넣는다. WSL2에서는 Windows
mount(`/mnt/c/...`)보다 WSL의 Linux filesystem을 권장한다.

Hermes가 사용하는 env 파일 위치를 확인한다.

```bash
hermes config env-path
```

다음 비밀정보가 아닌 실행 설정만 Hermes env 파일에 둔다.

```dotenv
HERMES_NEWS_WORKSPACE=<absolute-workspace-path>
HERMES_NEWS_SKILL_DIR=<absolute-installed-skill-path>
HERMES_NEWS_MAX_ITEMS=5
```

Telegram credential은 scanner가 검증 가능한 최소 권한 경계를 위해 workspace의
`.hermes-news/config/telegram.json`에 별도로 둔다.

```json
{
  "bot_token": "<bot-token>",
  "chat_id": "<chat-id>"
}
```

실제 값을 Git, Obsidian 문서, 작업 로그, cron prompt와 shell history에 기록하지
않는다. macOS/Linux/WSL2에서는 Hermes env 파일과 `telegram.json`을 `chmod 600`으로
제한한다. native Windows는 현재 사용자와 cron runner만 접근하도록 Windows ACL을
설정한다. PowerShell profile의 일시적 환경변수에만 의존하지 않는다.

`HERMES_NEWS_MAX_ITEMS=5`는 한 번의 agent 실행이 처리하는 최대 문서 수다. 초기에는
모델 비용과 실행 시간의 상한을 위해 5를 유지한다.

## 6. Skill 설치

Hermes의 [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)은
Agent Skills 공개 표준, GitHub direct install과 tap을 지원한다.

```bash
hermes skills inspect \
  skills-sh/dumbbelloper/hermes-agent/skills/hermes-news-automation
hermes skills install \
  skills-sh/dumbbelloper/hermes-agent/skills/hermes-news-automation
hermes skills list
```

목록에 `hermes-news-automation`이 있어야 한다. 개발 중인 Git checkout을 직접
사용할 때만 `skills.external_dirs`로 repository의 `skills/`를 연결한다.

## 7. Cron toolset

`hermes tools`에서 `cron` platform을 선택하고 다음 toolset만 활성화한다.

- `skills`
- `terminal`
- `file`
- `web`
- `delegation`

Cron toolset은 일반 CLI 설정과 별개다. 이 workflow는 browser automation,
access-control 우회, cron job 재귀 생성 또는 광범위한 시스템 관리 권한을 필요로
하지 않는다.

Writer와 Verifier는 fresh subagent context로 분리한다. 자세한 권한과 실행 방식은
[Hermes Delegation 공식 문서](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation)를
따른다.

## 8. Token 절약 pre-check 설치

Hermes cron의 pre-run script는 Hermes profile의 `scripts/` 아래에 있어야 한다.
설치된 Skill의 Python script를 복사한다. Skill을 업데이트하면 다시 복사한다.

macOS/Linux/WSL2:

```bash
mkdir -p ~/.hermes/scripts
cp "$HERMES_NEWS_SKILL_DIR/scripts/precheck.py" \
  ~/.hermes/scripts/hermes-news-precheck.py
chmod 700 ~/.hermes/scripts/hermes-news-precheck.py
```

native Windows PowerShell:

```powershell
$HermesScripts = Join-Path $env:LOCALAPPDATA "hermes\scripts"
New-Item -ItemType Directory -Force $HermesScripts | Out-Null
Copy-Item `
  (Join-Path $env:HERMES_NEWS_SKILL_DIR "scripts\precheck.py") `
  (Join-Path $HermesScripts "hermes-news-precheck.py") `
  -Force
```

pre-check는 source 수집과 delta queue를 먼저 만들고, 처리할 항목이 있을 때만
`wakeAgent: true`와 `run_id`를 반환한다. 변경이 없는 주기는 LLM을 호출하지 않는다.
이 방식은 Hermes의
[Scheduled Tasks pre-check](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron)
계약을 따른다.

## 9. Gateway 설치

### macOS

```bash
hermes gateway install
hermes gateway start
hermes gateway status
tail -f ~/.hermes/logs/gateway.log
```

Hermes가 생성한 `launchd` plist는 설치 시점의 PATH를 보존한다. Node나 다른 실행
도구를 나중에 설치했다면 `hermes gateway install`을 다시 실행한다.

### Linux

로그인 세션이 유지되는 개발 장비:

```bash
hermes gateway install
hermes gateway start
hermes gateway status
```

로그아웃 후에도 user service를 유지:

```bash
sudo loginctl enable-linger "$USER"
```

전용 서버에서 boot-time system service를 사용할 수도 있다.

```bash
sudo hermes gateway install --system
sudo hermes gateway start --system
sudo hermes gateway status --system
```

user gateway와 system gateway를 동시에 설치하지 않는다. 전용 service user가
workspace, Hermes profile과 credential을 모두 소유하도록 맞춘다. 공식 service
운영법은 [Hermes Messaging Gateway 문서](https://hermes-agent.nousresearch.com/docs/user-guide/messaging)를
따른다.

### Windows WSL2

WSL2 배포판에서 systemd를 활성화한 뒤 Linux 절차를 그대로 사용한다. Windows가
절전 또는 종료되거나 WSL instance가 정지하면 cron도 정지한다. 항상 켜진 운영은
native Linux 서버가 더 단순하다.

### Native Windows

PowerShell에서 실행한다.

```powershell
hermes gateway install
hermes gateway start
hermes gateway status
```

Hermes는 관리자 권한 없는 Windows Scheduled Task를 로그인 시점에 등록한다.
이 프로젝트는 native Windows에서 code-level lock backend와 공통 launcher를
제공하지만, 다음을 모두 통과하기 전에는 중요 운영 환경에 사용하지 않는다.

- 동일 snapshot 반복 시 신규 문서·Telegram 메시지 0건
- 동시 실행 시 하나만 lock 획득
- 한국어 문서 UTF-8 보존
- gateway 재시작 후 stale run 회수
- Telegram timeout의 `unknown` delivery 보존

## 10. 반복 작업 생성

아래 예시는 3시간마다 최대 5건을 처리한다. `<workspace-path>`는 초기화한 workspace의
실제 절대 경로로 치환한다. native Windows에서도 Hermes CLI는 동일 cron 명령을 제공하며 내부
terminal은 Git Bash를 사용한다.

```bash
hermes cron create "every 3h" \
  'Use $hermes-news-automation. If pre-check context contains a run_id, process that run completely. Publish only artifacts that pass independent verification. Return [SILENT] after successful completion.' \
  --skill hermes-news-automation \
  --script hermes-news-precheck.py \
  --workdir "<workspace-path>" \
  --deliver telegram \
  --name "Hermes payment news automation"
```

- `--workdir`는 초기화한 workspace의 절대 경로다.
- 정상 실행은 `[SILENT]`로 cron 자체의 중복 응답을 억제한다.
- 완성된 Obsidian 문서는 project notifier가 고정 Telegram chat으로 전송한다.
- cron agent 자체 실패는 Hermes의 `--deliver telegram` 대상으로 전달된다.
- Telegram home channel을 구성하지 않았다면 최초에는 `--deliver local`을 사용한다.

주기 변경:

```bash
hermes cron edit "Hermes payment news automation" --schedule "every 6h"
```

## 11. 최초 검증과 운영 승격

등록과 gateway 상태:

```bash
hermes cron list
hermes cron status
hermes gateway status
```

즉시 한 번 실행하고 이력을 확인한다.

```bash
hermes cron run "Hermes payment news automation"
hermes cron runs "Hermes payment news automation" --limit 20
```

설치와 workspace 검사:

```bash
python3 "$HERMES_NEWS_SKILL_DIR/scripts/run.py" doctor
python3 "$HERMES_NEWS_SKILL_DIR/scripts/run.py" validate-registry
python3 "$HERMES_NEWS_SKILL_DIR/scripts/run.py" validate-notes
```

운영 승격 조건:

- Vault validation issue 0건
- 동일 snapshot 반복 시 신규 문서와 Telegram 메시지 0건
- `.hermes-news/data/automation/runs/`에 완료 manifest 생성
- `.hermes-news/data/automation/deliveries.json`에 전송 결과 기록
- 관련성 또는 검증 실패 항목은 발행되지 않고 decision/run ledger에 남음
- OS 재시작 또는 gateway 재시작 후 다음 cron이 정상 수행됨

지원 표의 “1차 지원”은 설치만 된다는 뜻이 아니다. 해당 환경에서 위 smoke test를
최소 한 번 통과한 뒤 실제 운영으로 승격한다. 아직 이 프로젝트에서는 macOS의
단위·통합 검증만 수행했으며 Linux, WSL2, native Windows 실환경 smoke test는 남아
있다.

## 12. 중지와 복구

```bash
hermes cron pause "Hermes payment news automation"
hermes cron resume "Hermes payment news automation"
hermes cron remove "Hermes payment news automation"
```

특정 run 확인:

```bash
python3 "$HERMES_NEWS_SKILL_DIR/scripts/run.py" \
  automation-status --run-id <run-id>
```

native Windows에서는 위 설치 검사와 복구 명령의 `python3`만 `python`으로
바꾼다.

gateway 중단으로 logical lock이 만료되면 다음 실행이 기존 run을 `abandoned`로
기록하고 새 run을 시작한다. lock 파일을 수동 삭제하지 않는다. Telegram delivery가
`unknown`이면 중복 방지를 위해 자동 재전송하지 않는다.

## 13. 전원과 상시 실행

- macOS laptop은 전원과 네트워크를 유지하고 자동 sleep을 막아야 한다.
- Linux server는 systemd, filesystem 여유 공간, log rotation과 backup을 확인한다.
- WSL2는 Windows host와 WSL instance가 모두 실행 중이어야 한다.
- native Windows Scheduled Task는 사용자 로그인 기준이다. 무로그인 boot-time
  서버 운영은 Linux system service를 우선한다.

`.hermes-news/data/`는 checkpoint, run ledger와 delivery ledger를 포함하므로 backup
대상이다. 실행 중인 상태 디렉터리를 여러 host가 동시에 공유하지 않는다.

## 14. 보안 원칙

- source page는 비신뢰 데이터이며 그 안의 명령을 실행하지 않는다.
- Skill이 정한 고정 workflow 외 임의 shell 명령을 cron prompt에 추가하지 않는다.
- Telegram recipient와 credential 이름을 agent가 변경하지 못하게 한다.
- credential을 CLI argument, Git, 문서, artifact와 log에 넣지 않는다.
- 기존 수동 문서를 덮어쓰지 않는다.
- WAF, access control 또는 robots 정책을 우회하지 않는다.
- Skill과 controller를 업데이트하면 validator, test와 실환경 cron 1회를 다시
  실행한다.
