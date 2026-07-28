# Hermes Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

글로벌 결제 네트워크 생태계의 변화와 기술 트렌드를 꾸준히 수집하고 학습하기 위한 Obsidian 기반 지식 저장소입니다.

장기적으로 Visa, Mastercard, American Express, UnionPay, JCB 등의 공식 웹사이트와 기술 채널을 추적합니다. 현재 운영 수집기는 Visa, JCB, EMVCo, PCI Security Standards Council의 공식 공개 출처 4개에서 목록 메타데이터를 수집하며, 검토한 자료를 원문 링크, 한국어 요약과 학습 키워드가 포함된 Obsidian 문서로 정리하는 단계를 시작했습니다.

추적 범위는 글로벌 결제 네트워크를 시작점으로 하며, 향후 Ethereum, Solana 등의 블록체인 생태계, 스테이블코인, Samsung Pay, Apple Pay와 같은 디지털 월렛, HCE를 비롯한 결제 기술로 확장할 수 있습니다. 또한 국내 카드사와 관련 사업자의 서비스, 기술, 정책 및 시장 트렌드도 수집 대상에 포함할 수 있습니다.

현재 수집은 자동화됐지만 원문 본문 추출, 요약과 Obsidian 문서 작성은 아직 사람 검토가 필요한 초기 단계입니다. 향후 이 과정을 agent 및 skill 단위로 자동화합니다.

구체적인 수집·선별·문서화 설계는 [PROJECT_PLAN.md](./PROJECT_PLAN.md)에서 관리합니다.

전체 추적 대상과 초기 수집 범위는 [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md)에서 체크리스트로 관리합니다.

운영 수집 대상, 추가 구현 후보와 수집 제외 출처 및 판정 근거는 [SOURCE_CATALOG.md](./SOURCE_CATALOG.md)에서 관리합니다.

반복 실행 시 기존 문서를 판별하는 `record_id`, 원문 변경 감지와 Writer 멱등성 기준은 [NOTE_IDENTITY_POLICY.md](./NOTE_IDENTITY_POLICY.md)에서 관리합니다.

AI agent를 회사와 팀 업무에 안전하게 적용하기 위한 조직 수준의 통제 기준은 [ENTERPRISE_AI_GUARDRAILS.md](./ENTERPRISE_AI_GUARDRAILS.md)에서 관리합니다.

프로젝트에서 수행한 작업과 검증 결과는 [WORK_LOG.md](./WORK_LOG.md)에서 확인할 수 있습니다.

초기 공식 출처 18개를 대상으로 2026-07-24에 수행한 수집 방식, 메타데이터·원문 품질, 관련성 분류, 중복 및 장애 복구 검증 결과는 역사적 기준선인 [DATA_COLLECTION_VALIDATION_REPORT.md](./DATA_COLLECTION_VALIDATION_REPORT.md)에서 확인할 수 있습니다.

검증 결과를 코드로 승격한 최소 수집기의 실행법, 데이터 구조와 확장 경계는 [Automation/README.md](./Automation/README.md)에서 확인할 수 있습니다.

운영 출처의 첫 실제 수집에서 선별한 문서는 [2026-07-28 초기 수집 브리핑](./Digests/2026-07-28%20초기%20수집%20브리핑.md)에서 확인할 수 있습니다.

이 프로젝트는 [Apache License 2.0](./LICENSE)으로 공개됩니다.
