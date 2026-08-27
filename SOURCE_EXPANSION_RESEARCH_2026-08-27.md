# 2026-08-27 수집 출처 확장 탐색

> 기준일: 2026-08-27
>
> 상태: 1차 확장 구현·반복 수집 검증 완료

## 결론

수집 대상을 확장할 시점이다. 다만 일반 뉴스 매체를 더 붙이기보다 **공식 기술 변경, 국내 지급결제, 디지털 월렛, 결제 규격과 스테이블코인 인프라**로 확장하는 편이 현재 공백을 더 잘 메운다.

이번 1차 확장에서는 직접 구조화된 공식 endpoint와 높은 결제 신호 밀도를 함께 만족하는 다음 네 채널을 운영 Registry로 승격했다.

1. **한국은행 지급결제 조사연구자료 RSS**
2. **BIS/CPMI Publications RSS 1.0**
3. **Adyen Online Payments Release Notes RSS**
4. **Wise Platform API Changelog JSON**

네 출처 모두 offline fixture, allowlist, 실제 2회 수집과 두 번째 실행 멱등성을 확인했다. Stripe·Google Pay·Circle·Paxos·규격 artifact 추적은 후속 구현 후보로 유지한다.

일반 규제기관 전체 보도자료, Apple Developer 전체 릴리스, 범용 인증·블록체인 뉴스는 신호 대비 잡음이 커서 초기 확장에 넣지 않는 것이 적절하다.

## 확장이 필요한 근거

확장 전 운영 Registry는 공식 출처 9개와 편집 언론 4개, 총 13개였다. 이번 변경 후 [수집 출처 운영 분류](./SOURCE_CATALOG.md)와 [실행 설정](./Automation/config/sources.json)의 운영 범위는 공식 출처 13개와 편집 언론 4개, 총 17개다.

최근 automation manifest 30개를 집계한 결과는 다음과 같다.

- 공식 출처 신규 레코드: 15건
- 편집 언론 신규 레코드: 199건
- 전체 신규 레코드: 214건
- 공식 출처 중 30회 동안 신규 0건인 채널: EMVCo News, UnionPay Company News, UnionPay Market News, Visa Acceptance Devices iOS Releases, Visa Developer Release Notes
- 편집 언론 신규 레코드 중 PYMNTS 비중: 141건

현재 구조는 편집 언론의 발행량에 크게 의존하면서도, 월렛 API·PSP API·국내 지급결제·규격 문서 변경은 충분히 보지 못한다. 더 많은 일반 언론을 추가하면 발견량은 늘지만 검증 비용과 무관 기사도 함께 증가한다.

## 운영 승격 완료

### A1. 한국은행 지급결제 조사연구자료 RSS

- 공식 RSS: <https://www.bok.or.kr/portal/bbs/B0000232/news.rss?menuNo=200706>
- 공식 RSS 목록: <https://www.bok.or.kr/static/view/popup/rss_popup.html>
- 형식: RSS 2.0
- 메타데이터: 제목, canonical 게시물 URL, `pubDate`, 설명
- 신호: 원화 스테이블코인, 프로젝트 한강, 디지털 유로, 지급수단·모바일금융 이용행태 등 결제에 직접 연결
- 기존 adapter: `rss_atom` 재사용 가능
- 난점: 일부 게시물 본문이 “첨부파일 참고” 수준이므로 PDF 첨부 URL 추출과 checksum·본문 처리 경로가 필요
- 실수집 검증: 임시 Registry로 2회 연속 수집해 첫 실행 100건 신규·격리 0건, 두 번째 실행 100건 전부 `unchanged`·격리 0건을 확인
- 판정: **운영 승격 완료**

보완 채널로 한국은행의 [지급결제보고서 RSS](https://www.bok.or.kr/portal/bbs/P0000600/news.rss?menuNo=200072)를 같은 parser로 검증할 수 있다. 두 feed는 발행 빈도는 낮지만 신호 밀도가 높고, 국내 결제 생태계 공백을 직접 메운다.

### A2. BIS/CPMI Publications RSS

- 공식 RSS: <https://www.bis.org/doclist/cpmi_publs.rss>
- 형식: RSS 1.0/RDF, `dc:date`, 공식 원문 URL
- 신호: 국경간결제, 지급결제 통계, 청산·결제 인프라와 CPMI 정책 문서
- 구현: 공통 `rss_atom` adapter에 RDF root와 `dc:subject` 지원 추가
- 실수집 검증: 25건 수락·격리 0건, 두 번째 실행 25건 전부 `unchanged`
- 판정: **운영 승격 완료**

### A3. Adyen Online Payments Release Notes

- 공식 RSS: <https://docs.adyen.com/online-payments/release-notes.xml>
- 형식: RSS 2.0
- 신호: Checkout API, Web·iOS·Android·Flutter SDK, Apple Pay·Google Pay, 결제수단과 3-D Secure 변경
- 구현: `releaseNote` fragment를 `release_note` query identity로 승격해 fragment 제거 단계에서도 개별 릴리스를 구분
- 실수집 검증: 후보 613건 중 612건 수락·격리 0건·원문 중복 1건, 두 번째 실행 612건 전부 `unchanged`
- 판정: **운영 승격 완료**

### A4. Wise Platform API Changelog

- 공식 JSON: <https://docs.wise.com/page-data/changelog/data.json>
- 공식 문서: <https://docs.wise.com/changelog>
- 형식: 공개 JSON AST의 날짜별 `ChangelogEntry`
- 신호: 송금·payout·계좌·webhook schema·endpoint deprecation과 KYC API 변경
- 구현: 전용 `wise_changelog_json` adapter, 날짜별 stable query identity와 설명 텍스트 추출
- 실수집 검증: 38건 수락·격리 0건, 두 번째 실행 38건 전부 `unchanged`
- 판정: **운영 승격 완료**

## 후속 구현 권고

### B1. Stripe Changelog

- 공식 URL: <https://docs.stripe.com/changelog>
- 형식: 서버 렌더링 HTML
- 메타데이터: API version 날짜, 제품 category, 항목 제목, 항목별 canonical URL
- 확인 예: Payments, Issuing, Radar, Financial Connections, Connect 등 제품별 변경이 날짜와 함께 분리됨
- 장점: 결제 API contract, 결제수단, 3-D Secure, dispute, issuing 변화를 직접 제공
- 난점: 한 version에 항목이 많아 `Payments`, `Issuing`, `Radar`, `Financial Connections`, `Connect` 중심의 deterministic category filter가 필요
- 구현: 전용 `stripe_changelog_html` adapter와 fixture 필요
- 판정: **1차 신규 HTML adapter 대상**

### B2. Google Pay API Release Notes

- 공식 URL: <https://developers.google.com/pay/api/web/support/release-notes>
- 형식: 서버 렌더링 HTML
- 메타데이터: 날짜별 heading과 변경 설명
- 최신성 확인: 2026-08-12, 2026-08-05 항목이 존재
- 장점: 디지털 월렛 API 변화가 직접적이고, 기존 네트워크 뉴스와 중복이 낮음
- 난점: 날짜 아래 여러 변경을 안정 ID로 분리해야 하며 canonical URL은 같은 문서의 anchor일 수 있음
- 구현: 날짜 + 항목 fingerprint 기반 `google_pay_release_notes_html` adapter 필요
- 판정: **1차 신규 HTML adapter 대상**

## 기술 문서·필터형 후속 후보

### C1. 규격·문서 artifact 추적

| 후보 | 공식 URL | 가치 | 필요한 구현 |
| --- | --- | --- | --- |
| EMVCo Specifications | <https://www.emvco.com/specifications/> | EMV, 3-D Secure, tokenization, SRC 등 규격 버전 변화 | 문서 inventory, version·revision 추출, PDF checksum, semantic diff |
| PCI SSC Document Library | <https://www.pcisecuritystandards.org/document_library/> | PCI DSS·MPoC·CPoC·P2PE·3DS 보안 문서 변화 | 문서 목록 parser, 파일 URL·revision·checksum 추적 |
| Mastercard MDES Documentation | <https://developer.mastercard.com/product/mdes/> | tokenization 서비스와 운영 변경 | canonical 문서 inventory, release/effective date, API spec·PDF hash 추적 |

이 세 후보는 일반 뉴스보다 발행 빈도가 낮지만 한 번의 변경이 구현·보안·운영에 미치는 영향이 크다. 기존 뉴스 `Record` 계약에 억지로 맞추기보다 `artifact_version`, `effective_date`, `sha256`, `previous_sha256`를 가진 별도 기술 문서 수집 경로가 적합하다.

### C2. Circle 공식 블로그·개발 릴리스

- 공식 URL: <https://developers.circle.com/release-notes>, <https://www.circle.com/blog>
- 형식: 서버 렌더링 HTML
- 메타데이터: 제목, 날짜, topic, canonical 기사 URL
- 확인된 topic: Stablecoins, Developer, USDC, CPN
- 장점: USDC, CCTP, Circle Payments Network, stablecoin settlement 변화의 1차 출처
- 난점: 회사 홍보와 파트너 사례가 섞이므로 `USDC`, `Developer`, `CPN`, 결제·정산 topic allowlist가 필요
- 판정: **주제 제한을 전제로 2차 후보**

### C3. FIDO Alliance RSS

- 공식 RSS: <https://fidoalliance.org/feed/>
- 형식: RSS 2.0
- 최신성 확인: 2026-08-23까지 갱신
- 장점: passkey, 금융 인증, biometric identity 변화 보완
- 난점: 행사 회고·웨비나·일반 enterprise passkey 콘텐츠가 많음
- 판정: **payments/banking/authentication 주제 필터와 행사 제외 규칙을 전제로 2차 후보**

### C4. ECB Press RSS

- 공식 RSS: <https://www.ecb.europa.eu/rss/press.html>
- 형식: RSS 2.0
- 최신성 확인: 2026-08-26 tokenised financial market 관련 항목 존재
- 장점: digital euro, tokenised settlement, 유럽 지급결제 정책
- 난점: 통화정책·연설·거시경제 비중이 높음
- 판정: **digital euro, payments, settlement, tokenisation 등 deterministic prefilter를 전제로 2차 후보**

## 관찰용·보류 후보

| 후보 | 확인 결과 | 판정 |
| --- | --- | --- |
| CFPB Newsroom RSS | <https://www.consumerfinance.gov/about-us/newsroom/feed/>는 활성 RSS지만 소비자금융 전체를 다룸 | 카드·결제·wallet·remittance 규칙만 선별하는 3차 후보 |
| Federal Reserve All Releases | <https://www.federalreserve.gov/feeds/press_all.xml>는 활성 RSS지만 통화정책·은행 인가·제재가 대부분 | 전체 feed 직접 운영은 보류; 지급결제 전용 채널 발견 시 재검토 |
| OpenID Foundation RSS | <https://openid.net/feed/>는 활성이나 조직·정책·행사 콘텐츠가 넓음 | FAPI·OpenID4VC 규격 release 전용 경로를 먼저 탐색 |
| Apple Pay What’s New | <https://developer.apple.com/apple-pay/whats-new/>는 직접 접근 가능하고 신호는 높지만 항목별 게시일이 없음 | page hash + semantic diff 경로가 생긴 뒤 승격 |
| Apple Developer Releases RSS | <https://developer.apple.com/news/releases/rss/releases.rss>는 활성이나 OS·Xcode·TestFlight 전체 릴리스가 대부분 | Apple Pay 탐지용으로는 신호 밀도가 낮아 제외 |
| W3C Web Payments WG feed | <https://www.w3.org/blog/wpwg/feed/>는 HTTP 200이지만 item과 `lastBuildDate`가 비어 있음 | 현재 운영 제외 |

## 운영 구조 제안

확장 소스를 모두 같은 3시간 주기로 처리하지 않는다.

- **뉴스·release feed**: 3시간 주기, 기존 delta pipeline
- **HTML changelog**: 하루 1~2회, source-specific parser와 항목 fingerprint
- **PDF·규격 문서함**: 하루 또는 주 1회, checksum 우선 비교 후 의미 변경이 있을 때만 agent 호출
- **광범위 규제·인증 feed**: deterministic keyword/category filter를 통과한 항목만 queue 생성

source priority만으로는 비용을 충분히 제어할 수 없다. 수집 직후, agent를 깨우기 전에 다음 필드를 사용하는 source별 deterministic filter가 필요하다.

- include topic/category
- exclude event, webinar, hiring, investor conference, general monetary policy
- artifact type
- minimum effective-date/version signal
- source별 queue cap

## 권장 구현 순서

1. 완료 — 한국은행 지급결제 RSS, BIS/CPMI RSS, Adyen RSS, Wise JSON 운영 승격
2. 첨부 PDF가 있는 한국은행 게시물의 공식 PDF extractor와 checksum 계약
3. Stripe Changelog adapter와 Payments 계열 category filter
4. Google Pay Release Notes adapter와 날짜·항목 stable ID
5. Circle·Paxos release notes와 sitemap 기반 변경 감지
6. EMVCo·PCI·MDES artifact inventory와 hash ledger
7. 규제·인증 feed를 source별 deterministic filter와 함께 제한적으로 추가

각 단계는 [수집 출처 운영 분류](./SOURCE_CATALOG.md)의 승격 절차대로 adapter, offline fixture, allowlist, 빈 목록·파싱 실패 시 last-known-good 보존, 두 차례 실제 수집, 두 번째 실행의 멱등성을 검증한 뒤 운영 Registry에 반영한다.

## 알려진 한계

- 이번 변경은 구조화 endpoint 네 곳만 운영 승격했다. 나머지 후보는 Source Registry에 추가하지 않았다.
- 네 운영 출처의 단기 반복 수집은 검증했지만 장기 안정성과 발행 구조 변경은 source health로 계속 관찰해야 한다.
- PDF 첨부와 기술 문서 semantic diff는 현재 뉴스 원문 추출 경로와 별도 검증이 필요하다.
- 광범위 규제·인증 feed는 주제 필터 없이 운영하면 현재 PYMNTS 편중과 유사한 잡음 문제를 확대할 수 있다.
