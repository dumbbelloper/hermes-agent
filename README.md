# Hermes Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

글로벌 결제 네트워크 생태계의 변화와 기술 트렌드를 꾸준히 수집하고 학습하기 위한 Obsidian 기반 지식 저장소입니다.

장기적으로 Visa, Mastercard, American Express, UnionPay, JCB 등의 공식 웹사이트와 기술 채널을 추적합니다. 현재 운영 수집기는 공식 공개 출처 9개와 미국 금융·결제 편집 언론 4개, 총 13개 출처에서 목록 메타데이터를 수집하며, 검토한 자료를 원문 링크, 한국어 요약과 학습 키워드가 포함된 Obsidian 문서로 정리합니다.

추적 범위는 글로벌 결제 네트워크를 시작점으로 하며, 향후 Ethereum, Solana 등의 블록체인 생태계, 스테이블코인, Samsung Pay, Apple Pay와 같은 디지털 월렛, HCE를 비롯한 결제 기술로 확장할 수 있습니다. 또한 국내 카드사와 관련 사업자의 서비스, 기술, 정책 및 시장 트렌드도 수집 대상에 포함할 수 있습니다.

현재 수집, 신규·변경 queue, agent 관련성 판정, 독립 검증, Obsidian 문서 작성과 Telegram 알림을 하나의 무인 workflow로 연결했습니다. `record_id`와 `source_fingerprint`로 반복 실행의 중복과 원문 변경을 판정하며, 검증을 통과하지 못한 자료는 발행하지 않고 격리합니다. 실제 의미 검증은 [Hermes News Automation Skill](./skills/hermes-news-automation/SKILL.md)을 실행하는 Hermes Agent가 담당합니다.

Skill은 controller runtime을 자체 포함하므로 repository 전체를 복제하지 않고 설치할 수 있습니다. 공개 설치는 검증된 skills.sh identifier를 우선 사용하며 Hermes tap은 version별 검색 동작을 확인한 뒤 구독 경로로 사용할 수 있습니다. 설치, workspace 초기화, 업데이트와 release 기준은 [Skill 배포 가이드](./SKILL_DISTRIBUTION_GUIDE.md)에서 관리합니다.

구체적인 수집·선별·문서화 설계는 [PROJECT_PLAN.md](./PROJECT_PLAN.md)에서 관리합니다.

전체 추적 대상과 초기 수집 범위는 [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md)에서 체크리스트로 관리합니다.

운영 수집 대상, 추가 구현 후보와 수집 제외 출처 및 판정 근거는 [SOURCE_CATALOG.md](./SOURCE_CATALOG.md)에서 관리합니다.

반복 실행 시 기존 문서를 판별하는 `record_id`, 원문 변경 감지와 Writer 멱등성 기준은 [NOTE_IDENTITY_POLICY.md](./NOTE_IDENTITY_POLICY.md)에서 관리합니다.

AI agent를 회사와 팀 업무에 안전하게 적용하기 위한 조직 수준의 통제 기준은 [ENTERPRISE_AI_GUARDRAILS.md](./ENTERPRISE_AI_GUARDRAILS.md)에서 관리합니다.

프로젝트에서 수행한 작업과 검증 결과는 [WORK_LOG.md](./WORK_LOG.md)에서 확인할 수 있습니다.

초기 공식 출처 18개를 대상으로 2026-07-24에 수행한 수집 방식, 메타데이터·원문 품질, 관련성 분류, 중복 및 장애 복구 검증 결과는 역사적 기준선인 [DATA_COLLECTION_VALIDATION_REPORT.md](./DATA_COLLECTION_VALIDATION_REPORT.md)에서 확인할 수 있습니다.

검증 결과를 코드로 승격한 최소 수집기의 실행법, 데이터 구조와 확장 경계는 [Automation/README.md](./Automation/README.md)에서 확인할 수 있습니다.

macOS, Linux와 Windows에서 Hermes gateway와 cron으로 Skill을 계속 실행하는 방법과 플랫폼별 지원 등급은 [Hermes Agent 무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)에서 확인할 수 있습니다.

운영 출처의 첫 실제 수집에서 선별한 문서는 [2026-07-28 초기 수집 브리핑](./Digests/2026-07-28%20초기%20수집%20브리핑.md)에서 확인할 수 있습니다.

RSS·API 우선 기준으로 운영 출처를 9개로 확장하고 신규 채널에서 작성한 문서는 [2026-07-28 수집 출처 확장 브리핑](./Digests/2026-07-28%20수집%20출처%20확장%20브리핑.md)에서 확인할 수 있습니다.

미국 금융·결제 언론 4곳의 RSS 수집 결과와 신규 문서는 [2026-07-28 미국 금융 결제 언론 브리핑](./Digests/2026-07-28%20미국%20금융%20결제%20언론%20브리핑.md)에서 확인할 수 있습니다.

Skill의 첫 macOS 수동 end-to-end 실행에서 작성하고 Telegram 전송까지 검증한 문서는 [Visa FIFA World Cup 2026 결제 데이터](./Inbox/2026-07-22%20New%20Visa%20Data%20Reveals%20How%20the%20FIFA%20World%20Cup%202026%E2%84%A2%20Created%20Pop-Up%20Economies%20Across%20Canada%2C%20Mexico%20and%20the%20United%20States.md)에서 확인할 수 있습니다.

이 프로젝트는 [Apache License 2.0](./LICENSE)으로 공개됩니다.
