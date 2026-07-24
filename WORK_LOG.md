# 작업 로그

Hermes Agent 프로젝트에서 수행한 작업과 검증 결과를 시간순으로 기록한다.

## 2026-07-24 — 프로젝트 초기 설계와 Enterprise AI Guardrails

### 요청과 목적

- 글로벌 결제 생태계의 변화를 수집하고 Obsidian 문서로 정리하는 프로젝트 설명 작성
- 수집 대상, 수집 방법, 문서 형식, agent·skill 확장 방향 설계
- 전체 추적 범위와 초기 범위를 체크리스트로 관리
- GitHub 저장소 관리를 위한 제외 규칙 설정
- AI agent가 회사와 팀 업무에 접근할 때 필요한 조직 수준의 guardrail 설계
- 모든 Git push가 사람의 승인을 거치도록 Codex 전역 설정 적용

### 완료한 작업

- [x] 프로젝트 소개 작성
- [x] 수집·선별·요약·Obsidian 저장 파이프라인 설계
- [x] 전체 추적 범위와 초기 수집 범위 분리
- [x] GitHub용 `.gitignore` 작성
- [x] GitHub 원격 `main` push 상태 확인
- [x] Enterprise AI Agent Guardrails 작성
- [x] Codex 전역 sandbox와 승인 기본값 설정
- [x] Git 실행의 전역 승인 규칙 작성 및 정책 엔진 테스트
- [x] 향후 작업 로그 작성을 프로젝트 지속 지침에 반영

### 주요 문서

- [README.md](./README.md)
- [PROJECT_PLAN.md](./PROJECT_PLAN.md)
- [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md)
- [ENTERPRISE_AI_GUARDRAILS.md](./ENTERPRISE_AI_GUARDRAILS.md)
- [AGENTS.md](./AGENTS.md)
- [.gitignore](./.gitignore)

### Enterprise Guardrails 설계 내용

다음 범위를 개인 CLI 설정이 아닌 조직 수준의 통제로 정리했다.

- G0~G4 위험 등급과 승인 정책
- Source control과 협업
- CI/CD, release와 production 배포
- Infrastructure as Code와 cloud
- Kubernetes와 runtime
- Database와 데이터
- Identity, secret과 보안 정책
- 고객 및 외부 커뮤니케이션
- 결제, 재무와 상거래
- 보안 운영과 사고 대응
- 역할 분리, 감사, 복구, break-glass
- Codex command rule의 역할과 우회 가능성

통제 설계는 NIST AI RMF, NIST SP 800-53, OWASP Agentic AI, GitHub, HashiCorp, Kubernetes, OPA, AWS IAM, SLSA, npm, PCI SSC 공식 자료를 기준으로 작성했다.

### Codex 전역 설정 변경

사용자 전역 설정 파일:

```text
/Users/dumbbelloper/.codex/config.toml
```

적용한 기본값:

```toml
sandbox_mode = "workspace-write"
approval_policy = "on-request"
approvals_reviewer = "user"

[sandbox_workspace_write]
network_access = false
```

기존 설정 백업:

```text
/Users/dumbbelloper/.codex/config.toml.backup-20260724
```

전역 Git 규칙:

```text
/Users/dumbbelloper/.codex/rules/production-guardrails.rules
```

정책은 sandbox 경계를 넘어야 하는 모든 Git 실행을 `prompt`로 처리한다. 단순한 `["git", "push"]` 규칙보다 넓게 설정해 다음 형태를 포함한다.

- `git push` 뒤의 모든 option, remote, refspec
- `--force-with-lease`, `--force`, `--mirror`
- remote branch와 tag 삭제
- `git -C <path> push`
- `git -c <config> push`
- Git alias
- `/usr/bin/git`
- `/opt/homebrew/bin/git`

### 검증 결과

Codex `execpolicy`로 다음 명령이 모두 `prompt`로 판정되는 것을 확인했다.

```text
git push --force-with-lease origin main
git -C /tmp/example push origin main
/usr/bin/git push --mirror
/opt/homebrew/bin/git push origin main
```

비Git 명령인 `gh pr view 1`은 해당 규칙과 일치하지 않았다. 새 전역 설정을 적용한 상태에서 Codex CLI가 정상적으로 시작되고 규칙 파일을 읽는 것도 확인했다.

GitHub 상태 확인 당시 로컬 `main`과 원격 `origin/main`은 동일한 커밋 `e5934d2`를 가리켰다.

### 주요 결정

1. Agent의 로컬 prompt는 최종 보안 경계가 아니다.
2. Production 안전은 GitHub ruleset, deployment approval, IAM, RBAC, database 권한 등 대상 시스템에서 강제해야 한다.
3. 모든 Git 실행을 규칙 대상으로 삼아 subcommand 앞에 global option이 오는 형태와 Git alias를 포함한다.
4. Project 내부 작업은 자동화하되 network와 workspace 외부 접근은 기본 승인 대상으로 둔다.
5. G4 작업은 agent에게 실행 credential을 제공하지 않는 것을 기본값으로 한다.

### 알려진 한계

- Codex command prefix 규칙은 별도 프로그램이나 script가 내부에서 Git을 실행하는 모든 간접 경로를 완전히 증명하지 못한다.
- 다른 AI 제품, 수동 terminal, CI runner, 유출된 credential에는 Codex 전역 규칙이 적용되지 않는다.
- `danger-full-access`, 무제한 network, 별도 binary 복사본은 로컬 규칙의 보호를 약화할 수 있다.
- 따라서 GitHub branch protection, required review와 production credential 분리가 추가로 필요하다.
- 전역 설정 변경은 새 Codex 세션에서 가장 확실하게 반영된다.

### 다음 작업

- [ ] GitHub `main` branch ruleset 설정
- [ ] GitHub Actions와 production environment 사용 시 required reviewer 설정
- [ ] 조직과 업무에 맞는 G2·G3·G4 승인자 매트릭스 확정
- [ ] 실제 사용하는 cloud, Kubernetes, database, package registry별 강제 정책 작성
- [ ] Source Registry의 실제 공식 URI 조사

### Git 작업

작업 브랜치:

```text
docs/enterprise-ai-guardrails
```

파일별 한글 커밋:

- `76d622c` — 프로젝트 작업 기록 지침 추가 (`AGENTS.md`)
- `285ffb0` — 엔터프라이즈 AI 가드레일 문서 추가 (`ENTERPRISE_AI_GUARDRAILS.md`)
- `9c8d934` — 프로젝트 설계에 가드레일 기준 연결 (`PROJECT_PLAN.md`)
- `9d44f11` — 프로젝트 주요 문서 링크 추가 (`README.md`)
- `ae405bf` — 초기 작업 내역과 검증 결과 기록 (`WORK_LOG.md`)
- `f70158d` — 가드레일 문서 서식 정리 (`ENTERPRISE_AI_GUARDRAILS.md`)

각 커밋은 하나의 파일만 변경하도록 분리했다. `WORK_LOG.md` 역시 별도 커밋으로 관리한다.

생성한 Pull Request:

- [#1 엔터프라이즈 AI 에이전트 가드레일 문서화](https://github.com/dumbbelloper/hermes-agent/pull/1)

작업 브랜치를 `origin/docs/enterprise-ai-guardrails`로 push했고, GitHub CLI 재인증 후 PR을 생성했다.
