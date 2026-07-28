---
note_schema_version: "1.0"
record_id: "d34d1292af3beb69123b4bf56480639f6317fe9d4abb9ed61b49122a1314236b"
source_fingerprint: "3cb1b9309afd3debd24978f759cbd05e54447f1284f0fed070be052e0d5838bb"
source: "Visa"
source_id: "visa-acceptance-devices-ios-releases"
source_type: "official-github-release-atom"
canonical_url: "https://github.com/visa/acceptance-devices-ios-sdk/releases/tag/3.7.0"
original_url: "https://github.com/visa/acceptance-devices-ios-sdk/releases/tag/3.7.0"
published_at: "2026-05-29"
collected_at: "2026-07-28T12:23:18+09:00"
first_collected_at: "2026-07-28T12:23:18+09:00"
last_checked_at: "2026-07-28T12:23:18+09:00"
language: "en"
discovery_method: "official-atom-feed"
verification_status: "official-release-verified"
created_by: "manual"
generator: "manual-review"
generator_version: "1.0"
topics:
  - tap-to-pay
  - ios
  - offline-payments
  - merchant-acquiring
importance: "high"
status: "draft"
---

# Visa Acceptance Devices iOS SDK 3.7.0

## 원문

- [GitHub Release 3.7.0](https://github.com/visa/acceptance-devices-ios-sdk/releases/tag/3.7.0)
- 발행: 2026-05-29
- 출처: Visa / acceptance-devices-ios-sdk
- 수집·검증: 공식 GitHub Release Atom feed에서 발견하고 릴리스 본문 확인

## 요약

Visa Acceptance Devices iOS SDK 3.7.0은 iPhone 기반 Tap to Pay 통합에서 운영 복원력과 merchant onboarding 가시성을 개선했다.

새 공개 API는 SDK session을 필요할 때 갱신할 수 있게 한다. 네트워크 연결이 가능한 상태에서 초기화할 때도 session을 자동 갱신해, 기기 재시작 뒤 offline 거래가 유효하지 않은 session 때문에 실패하던 문제를 줄인다. Enrollment의 device preparation 진행률도 외부에 노출해 가맹점에 실제 진행 상태를 표시할 수 있고, `ActivationStatus`에는 merchant ID가 추가됐다.

오류 처리 측면에서는 전화 수신 등으로 card-present 거래가 중단될 때 구체적인 cancel code를 전달한다. 거래내역 날짜 필터의 HTTP 400 오류, 연속 offline 거래 실패 후 빈 화면, activation 입력값 autocorrect 문제도 수정됐다. 스페인과 멕시코 스페인어 localization이 추가됐으며 새 API는 breaking change가 아니라고 명시됐다.

## 왜 중요한가

Tap to Pay는 결제 승인 기능만으로 운영되지 않는다. 기기 재시작, 불안정한 연결, enrollment 중단과 통화 interruption 같은 모바일 운영 조건이 승인 성공률과 가맹점 경험을 결정한다. 이 릴리스는 softPOS 통합에서 session lifecycle, offline mode와 observable onboarding을 별도 설계 대상으로 봐야 한다는 근거다.

## 기술 학습 키워드

- Tap to Pay on iPhone — 별도 결제 단말 없이 iPhone의 NFC로 contactless 결제를 받는 방식
- Store and Forward — 연결이 없을 때 거래를 저장한 뒤 복구 시 전달하는 처리 방식
- Session lifecycle — SDK 인증·상태 session의 생성, 갱신과 만료 과정
- Enrollment — 가맹점과 기기를 결제 서비스에 등록하고 준비하는 절차
- Card-present cancellation — 대면 결제 중 사용자 또는 기기 이벤트로 거래가 중단되는 경우

## 확인할 점

- session 자동 갱신 실패 시 retry와 merchant 안내 정책
- offline 거래의 금액·건수 제한, 위험 부담과 최종 승인 주체
- 공개된 enrollment 진행률 단계가 Android SDK와 동일한지
- 구체화된 cancel code를 분석·알림 체계에 연결하는 방법
