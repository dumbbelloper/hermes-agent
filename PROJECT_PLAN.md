# Hermes Agent 프로젝트 설계

> 기준일: 2026-07-28
>
> 상태: Phase 0 완료 · Phase 1 운영 출처 13개 확정 · Telegram 알림 검증

## 1. 목표

바쁜 일상에서도 글로벌 결제 네트워크 생태계의 중요한 변화를 놓치지 않도록 다음 과정을 반복 가능하게 만든다.

1. 공식 채널과 신뢰할 수 있는 뉴스에서 신규 자료를 수집한다.
2. 중복과 저가치 자료를 제거하고 중요도를 판정한다.
3. 원문의 의미를 보존한 한국어 요약과 학습 키워드를 작성한다.
4. Obsidian에서 검색하고 연결하기 쉬운 Markdown 문서로 저장한다.
5. 매일 자동 실행하되 실패와 누락을 사람이 확인할 수 있게 한다.

## 2. 추적 범위

전체 추적 후보와 초기 수집 범위의 선정 상태는 [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md)에서 관리한다.
실제 운영·후보·제외 출처와 판정 근거는 [SOURCE_CATALOG.md](./SOURCE_CATALOG.md)에서 관리한다.

### 우선 추적 대상

- Visa
- Mastercard
- American Express
- UnionPay
- JCB

### 출처 우선순위

1. 공식 개발자 문서, 제품 문서, 표준 및 규격
2. 공식 뉴스룸, 보도자료, 기업 블로그
3. 공식 GitHub 저장소와 릴리스
4. 공식 YouTube 채널
5. 규제기관, 표준화 기구, 거래소 등 1차 출처
6. 신뢰할 수 있는 전문 매체와 일반 뉴스

공식 자료를 우선하며 뉴스는 공식 발표의 맥락, 시장 반응, 경쟁 구도를 보완하는 용도로 사용한다.

## 3. 수집 전략

출처마다 가장 안정적인 공개 인터페이스를 선택한다.

| 출처 유형 | 1차 수집 방식 | 대체 방식 | 수집할 정보 |
| --- | --- | --- | --- |
| 공식 사이트·블로그 | RSS/Atom 또는 sitemap | 목록 페이지 변경 감지 | 제목, URL, 게시일, 본문, 작성 주체 |
| 뉴스룸·보도자료 | RSS 또는 목록 페이지 | 검색 API/검색 엔진 | 제목, URL, 게시일, 본문 |
| GitHub | GitHub API의 release/event 조회 | Atom feed | 저장소, 버전, 변경 내역, 게시일 |
| YouTube | 채널 RSS | YouTube Data API | 영상 제목, URL, 게시일, 설명, 자막 유무 |
| 뉴스 | 허가된 RSS/API | 검색 결과의 원문 링크 | 매체, 제목, URL, 게시일, 본문 |

### 수집 원칙

- robots.txt, 서비스 약관, API 사용 제한과 콘텐츠 저작권을 준수한다.
- 원문 전체를 Vault에 복제하지 않고 링크, 메타데이터, 자체 요약 중심으로 저장한다.
- URL 정규화와 원문 고유 ID로 같은 자료의 중복 저장을 막는다.
- 게시 시각과 최초 발견 시각을 별도로 기록한다.
- 동적 페이지나 수집 실패는 즉시 브라우저 자동화로 우회하지 않고 실패 큐에 남긴다.
- 로그와 체크포인트를 남겨 중단 이후에도 마지막 성공 지점부터 재개한다.

## 4. 처리 파이프라인

```text
Source Registry
    → Fetch
    → Normalize
    → Deduplicate
    → Relevance Filter
    → Enrich & Summarize
    → Validate
    → Write Markdown
    → Daily Digest
```

### 단계별 책임

1. **Source Registry**
   - 추적할 조직, 채널, URL, 수집 방식, 실행 주기, 언어를 관리한다.
2. **Fetch**
   - 마지막 실행 이후 새로 발행된 항목의 메타데이터와 접근 가능한 원문을 가져온다.
3. **Normalize**
   - 날짜, 조직명, URL, 콘텐츠 유형을 공통 스키마로 변환한다.
4. **Deduplicate**
   - canonical URL, 외부 ID, 제목 유사도, 본문 해시로 중복을 판정한다.
5. **Relevance Filter**
   - 결제 기술, 네트워크 정책, 제품, 보안, 표준, 규제, 파트너십 등 관심 범위와의 관련성을 평가한다.
6. **Enrich & Summarize**
   - 핵심 내용, 의미, 기술 학습 키워드를 원문 근거 안에서 작성한다.
7. **Validate**
   - 제목과 원문 링크 존재 여부, 날짜 형식, 요약의 근거성, 중복 여부를 검사한다.
8. **Write Markdown**
   - 정해진 템플릿으로 원자적 문서를 생성한다.
9. **Daily Digest**
   - 당일 신규 문서 중 중요한 변화를 한 문서에서 훑어볼 수 있게 연결한다.

## 5. 문서 규격 초안

### 파일과 제목

- 문서의 H1 제목은 원문의 제목을 그대로 사용한다.
- 파일명에는 운영체제에서 사용할 수 없는 문자를 치환한다.
- 같은 제목이 존재하면 게시일 또는 짧은 콘텐츠 ID를 파일명에 추가한다.
- 원문 제목을 번역하지 않는다. 필요한 경우 본문 요약에서 한국어로 뜻을 설명한다.

### Frontmatter

```yaml
---
source: "Visa"
source_type: "official-blog"
original_url: "https://example.com/original"
published_at: "2026-07-24"
collected_at: "2026-07-24T09:00:00+09:00"
language: "en"
topics:
  - tokenization
  - digital-identity
importance: "high"
status: "reviewed"
---
```

필수 필드는 `source`, `source_type`, `original_url`, `published_at`, `collected_at`이다. `importance`와 `status`는 자동화 초기에는 검토 가능한 값으로 유지한다.

### 본문 템플릿

```markdown
# 원문 제목 그대로

## 원문

- [원문 보기](https://example.com/original)
- 발행: YYYY-MM-DD
- 출처: Organization / Channel

## 요약

원문에서 확인되는 핵심 내용을 한국어로 간결하게 정리한다.

## 왜 중요한가

결제 생태계, 경쟁 구도, 운영 또는 제품 관점의 의미를 정리한다.

## 기술 학습 키워드

- [[Tokenization]] — 이 자료에서 알아야 할 이유
- [[Passkey]] — 이 자료에서 알아야 할 이유

## 확인할 점

- 추가 검증이나 후속 추적이 필요한 내용
```

원문에 기술 학습 요소가 없다면 `기술 학습 키워드` 절은 생략할 수 있다. 추론이나 해석은 원문에 나온 사실과 구분해 표현한다.

## 6. 제안 폴더 구조

```text
.
├── README.md
├── PROJECT_PLAN.md
├── Inbox/
│   └── 수집 직후 검토 전 문서
├── Sources/
│   └── 조직 및 채널별 출처 설명
├── Notes/
│   ├── Visa/
│   ├── Mastercard/
│   ├── American Express/
│   ├── UnionPay/
│   ├── JCB/
│   └── Industry/
├── Digests/
│   └── 일간·주간 요약
├── Concepts/
│   └── 기술 및 산업 개념 노트
├── Templates/
│   └── 문서 템플릿
└── Automation/
    └── 설정, 상태, 로그 및 실행 코드
```

초기에는 폴더를 모두 만들지 않는다. 실제 수집 샘플로 문서 흐름을 검증한 뒤 필요한 폴더만 생성한다.

## 7. Agent와 Skill 경계

Agent와 skill의 권한, 승인, 운영 환경 및 감사 기준은 [ENTERPRISE_AI_GUARDRAILS.md](./ENTERPRISE_AI_GUARDRAILS.md)를 따른다.

### Agent 후보

- **Collector Agent**: 여러 수집 skill을 실행하고 체크포인트와 실패를 관리한다.
- **Curator Agent**: 관련성, 중복, 중요도를 판단한다.
- **Writer Agent**: 요약과 키워드를 작성하고 Markdown 규격을 검증한다.
- **Digest Agent**: 신규 문서를 묶어 일간·주간 브리핑을 만든다.

### Skill 후보

- RSS/Atom 수집
- sitemap 및 목록 페이지 수집
- GitHub release 수집
- YouTube 메타데이터·자막 수집
- 웹 문서 본문 추출
- URL 정규화와 중복 탐지
- 결제 산업 관련성 분류
- 근거 기반 한국어 요약
- Obsidian 문서 생성과 링크 연결
- 실행 결과 및 품질 검증

Agent는 작업 순서와 상태를 조정하고, skill은 입력과 출력이 명확한 단일 기능으로 설계한다.

## 8. 실행 및 검토 정책

- 기본 실행 주기: 매일 1회
- 수집 범위: 마지막 성공 시각 이후 발행 또는 수정된 항목
- 자동 저장 위치: 초기에는 `Inbox/`
- 사람 검토 후 이동: `Notes/<Organization>/`
- 중요 항목: 일간 Digest에 포함
- 실패 항목: 원인과 재시도 가능 여부를 기록
- 동일 원문 업데이트: 새 문서를 만들기보다 기존 문서의 변경 이력을 남기는 방식을 우선 검토

완전 자동 발행보다 `수집 → 초안 생성 → 사람 검토` 방식으로 시작하고, 품질이 안정된 출처부터 자동 승격한다.

## 9. 단계별 구현 계획

### 구현 현황 — 2026-07-28

- [x] Phase 0 공식 출처 조사와 수집 품질 검증
- [x] versioned Source Registry와 공식 도메인 allowlist
- [x] Visa HTML, JCB JSON, EMVCo RSS, PCI SSC RSS adapter
- [x] 공통 스키마, URL·날짜 정규화와 레코드 검증
- [x] 원본·snapshot·누적 정상 상태·격리·source health 저장
- [x] 빈 snapshot과 수집 실패 시 마지막 정상 상태 보존
- [x] CLI와 네트워크 없는 fixture 회귀 테스트
- [x] 공식 9개·편집 언론 4개, 추가 구현 후보와 수집 제외 출처 분류
- [x] 수집 `record_id`를 이용한 Vault 문서 인덱스와 중복 작성 방지 판정
- Phase 1 최소 수집기 부분 완료 — 메타데이터 수집 완료, Inbox 자동 작성 미완료
- [x] 선별 GitHub Release Atom 수집
- [ ] 원문 본문 수집과 Obsidian Inbox 문서 생성
- [x] 환경변수 기반 Telegram 문서 알림
- [ ] scheduler, retry와 운영 지표

구현 세부 사항과 실행법은 [Automation/README.md](./Automation/README.md)에서 관리한다.

### Phase 0 — 설계 검증

- [x] 추적 대상별 공식 채널 목록 작성
- [x] 출처의 RSS, sitemap, API 제공 여부 확인
- [x] 590건 메타데이터와 136건 원문 추출 표본 검증
- [x] 관련성 보존 기준과 자동 제외 원칙 확정
- [x] 접근 차단·브라우저 의존 출처를 운영 범위에서 제외

### Phase 1 — 최소 수집기

- [x] 운영 Source Registry 정의
- [x] RSS/Atom, 공식 JSON과 정적 HTML 수집 구현
- [x] 상태 저장, URL 정규화, 중복 제거 구현
- [x] 선별한 GitHub Release Atom 수집 구현
- [ ] 원문 링크 중심의 Inbox 문서 생성 자동화

### Phase 2 — 요약 및 품질 관리

- 본문 추출과 한국어 요약 추가
- 기술 키워드 추출 및 Concepts 연결
- 스키마와 링크 자동 검증
- 사람이 수정한 문서와 자동 생성 문서의 충돌 방지

### Phase 3 — 채널 확장

- YouTube와 비-RSS 공식 사이트 지원
- 뉴스 및 규제기관 출처 추가
- 일간·주간 Digest 생성

### Phase 4 — 운영 자동화

- 스케줄 실행
- 실패 알림과 재시도
- 출처별 성공률, 신규 항목 수, 중복 제거 수 관측
- 회귀 테스트와 요약 품질 샘플링

## 10. 결정 현황

| 항목 | 상태 | 결정 또는 남은 선택 |
| --- | --- | --- |
| 구현 언어와 런타임 | 결정 | Python 3.9 이상, runtime dependency 없음 |
| 현재 실행 환경 | 결정 | 로컬 수동 실행, `Automation/data/`에 상태 저장 |
| 운영 출처 | 결정 | 직접 접근 가능한 공식 출처 9개와 편집 언론 4개, 세부 기준은 [SOURCE_CATALOG.md](./SOURCE_CATALOG.md) |
| 차단 출처 처리 | 결정 | WAF 우회, 검색 인덱스와 브라우저 자동화 폴백 없이 제외 |
| 문서 식별과 중복 방지 | 결정 | `record_id`, `source_fingerprint`와 실행 시 Vault index 사용. 세부 기준은 [NOTE_IDENTITY_POLICY.md](./NOTE_IDENTITY_POLICY.md) |
| 문서 승인 | 임시 결정 | `Inbox/` 초안을 사람이 검토한 뒤 `Notes/`로 이동 |
| LLM 정책 | 미결정 | 사용 위치, 모델, 비용, 근거 보존과 민감정보 기준 필요 |
| 중요도·일간 상한 | 미결정 | 초기 문서 표본을 검토한 뒤 확정 |
| 원문 수정·삭제 | 미결정 | 기존 노트 보존과 변경 이력 정책 필요 |
| 운영 자동화 환경 | 미결정 | 로컬 scheduler, GitHub Actions, 별도 서버 중 선택 |

## 11. 현재 문서 작성 작업

운영 출처 13개의 최신 자료 중 결제 기술·표준·보안 변화와 직접 관련된 항목을 소량 선별해 `Inbox/` 초안을 작성한다. 현재 누적 1,594건에서 12건을 문서화했다.

- [x] 안정적인 신규 항목 탐지와 원문 제목·링크 보존 검증
- [ ] 한국어 요약만으로 핵심 변화를 이해할 수 있는지 검토
- [ ] 기술 키워드가 실제 학습 노트로 연결되는지 검토
- [ ] 사람이 검토하기 적절한 문서 수와 중요도 기준 확정
- [ ] 같은 사건의 조직 간 발표를 연결하는 방식 검증

초기 초안 검토 결과를 바탕으로 문서 템플릿과 자동 생성 범위를 확정한다.
