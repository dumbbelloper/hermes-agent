# 수집 출처 운영 분류

> 기준일: 2026-07-28
>
> 상태: 운영 범위 확정

이 문서는 Hermes Agent가 실제로 자동 수집할 공식 출처, 추가 구현 후 검토할 후보와 운영에서 제외할 출처를 관리한다. 조사 범위는 [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md), 과거 품질 실험은 [DATA_COLLECTION_VALIDATION_REPORT.md](./DATA_COLLECTION_VALIDATION_REPORT.md), 실행 설정은 [Automation/config/sources.json](./Automation/config/sources.json)을 따른다.

## 1. 판정 기준

### 운영

다음 조건을 모두 만족해야 한다.

- 로그인, cookie, API key 없이 공식 HTTPS URI에 직접 접근할 수 있다.
- RSS·Atom, 공식 JSON 또는 서버가 완성한 정적 HTML에서 항목을 재현 가능하게 추출할 수 있다.
- 제목, 공식 원문 URL과 게시일을 안정적으로 얻을 수 있다.
- 허용 도메인, 빈 목록, 과도한 격리와 마지막 정상 상태 보존 검사를 통과한다.
- fixture 회귀 테스트와 실제 반복 수집에서 멱등성을 확인했다.

### 추가 구현 후보

일반 HTTP로 직접 접근할 수 있고 가치가 있지만 전용 항목 파서, 변경 감지 또는 회귀 테스트가 아직 없다. 후보는 운영 수집이나 문서 생성에 사용하지 않으며 구현과 실제 반복 검증을 통과한 뒤 운영으로 승격한다.

### 제외

다음 중 하나에 해당하면 미련 없이 운영 범위에서 제외한다.

- Akamai, Cloudflare 등 WAF의 challenge·차단을 우회해야 한다.
- 브라우저 렌더링, 검색 인덱스, 비공식 mirror 또는 로그인 세션이 필요하다.
- 목록 URI가 없거나 현재 공식 개발자 출처를 확인할 수 없다.
- 업데이트가 드물거나 마케팅·범용 코드 비중이 높아 신호 대비 잡음이 크다.

차단 출처를 공격적으로 재시도하거나 user-agent·브라우저 위장으로 우회하지 않는다. 제외 판정은 명시적인 재검토 작업이 있기 전까지 유지한다.

## 2. 운영 수집 출처

| Source ID | 조직·채널 | 공식 URI | 방식 | 판정 근거 |
| --- | --- | --- | --- | --- |
| `visa-press` | Visa Press Releases | [공식 목록](https://usa.visa.com/about-visa/newsroom/press-releases-listing.html) | 정적 HTML | 일반 HTTP 200, 제목·URL·게시일 추출, 실제 반복 수집과 회귀 테스트 통과 |
| `visa-developer-release-notes` | Visa Developer Release Notes | [공식 Release Notes](https://developer.visa.com/site/release_notes) | 정적 HTML | 월별 제품·API 변경과 날짜 추출, 의미 query로 안정 ID 분리, 반복 수집 통과 |
| `visa-acceptance-devices-ios-releases` | Visa Acceptance Devices iOS SDK | [GitHub Releases Atom](https://github.com/visa/acceptance-devices-ios-sdk/releases.atom) | Atom | 결제 SDK allowlist 저장소, 2026년 활성 release와 상세 변경 내역, 반복 수집 통과 |
| `amex-newsroom` | American Express Newsroom | [공식 AEM model JSON](https://www.americanexpress.com/en-us/newsroom/index.model.json) | 공식 JSON | 홈페이지가 사용하는 공개 구조화 모델, 제목·URL·최초 게시일·카테고리 제공, 반복 수집 통과 |
| `unionpay-company-news` | UnionPay Company News | [공식 JSON](https://www.unionpayintl.com/wap/newsList/en_companyNews.json) | 공식 JSON | Media Center가 사용하는 공개 JSON, 2026년까지 갱신, 779건 반복 수집 통과 |
| `unionpay-market-news` | UnionPay Market News | [공식 JSON](https://www.unionpayintl.com/wap/newsList/en_marketUpdate.json) | 공식 JSON | Media Center가 사용하는 공개 JSON, 2026년까지 갱신, 140건 반복 수집 통과 |
| `jcb-press` | JCB Press | [공식 JSON](https://www.global.jcb/en/press/news_file.json) | 공식 JSON | 일반 HTTP 200, 구조화 필드 제공, 실제 반복 수집과 회귀 테스트 통과 |
| `emvco-news` | EMVCo News | [공식 RSS](https://www.emvco.com/news/feed/) | RSS | 일반 HTTP 200, 표준 feed, 실제 반복 수집과 RSS·Atom 테스트 통과 |
| `pci-blog` | PCI SSC Blog | [공식 RSS](https://blog.pcisecuritystandards.org/rss.xml) | RSS | 일반 HTTP 200, 표준 feed, 실제 반복 수집과 RSS 테스트 통과 |

이 9개 출처가 현재 고정된 운영 범위다. 2026-07-28 두 차례 실수집에서 9/9 성공, 누적 1,544건, 격리 0건을 확인했고 두 번째 실행은 전부 `unchanged`였다. Registry 변경은 이 문서의 판정과 코드·fixture 검증을 함께 갱신해야 한다.

## 3. 추가 구현 후보

| 조직·채널 | 공식 URI | 현재 상태 | 승격 조건 |
| --- | --- | --- | --- |
| EMVCo Specifications | [공식 검색](https://www.emvco.com/specifications/) | 직접 접근 가능, 검색 페이지로 redirect | 규격명·버전·수정일·문서 URL 단위 parser와 파일 변경 검증 |
| PCI SSC Document Library | [공식 문서함](https://www.pcisecuritystandards.org/document_library/) | 직접 접근 가능 | 문서명·버전·수정일·파일 URL 단위 parser와 파일 변경 검증 |
| Visa Developer Use Cases | [공식 Use Cases](https://developer.visa.com/use-cases) | 정적 HTML에서 제목·URL 추출 가능하나 게시일 없음 | 공식 게시일 또는 별도 변경일을 재현 가능하게 얻을 수 있을 때 승격 |

## 4. 수집 제외 출처

| 조직·채널 | 공식 URI | 제외 사유 | 재검토 조건 |
| --- | --- | --- | --- |
| Mastercard Press Releases | [공식 목록](https://www.mastercard.com/us/en/news-and-trends/press.html) | 일반 HTTP에서 Akamai `Access Denied` 403. 검색 인덱스·브라우저 폴백을 운영하지 않음 | 인증 없는 공식 RSS·JSON·API 제공 |
| Mastercard Developer Products | [공식 포털](https://developer.mastercard.com/products) | HTML에 항목이 없는 JavaScript 셸, 브라우저 렌더링 필요 | 서버 렌더링 목록 또는 공식 feed/API 제공 |
| American Express Developer Documentation | [공식 포털](https://developer.americanexpress.com/documentation) | HTML에 문서 본문이 없는 JavaScript 셸, 브라우저 렌더링 필요 | 서버 렌더링 목록 또는 공식 feed/API 제공 |
| UnionPay 개발자 문서 | [공식 홈페이지](https://www.unionpayintl.com/en/) | 현재 사용 가능한 공개 개발자 포털 URI를 확인하지 못함 | 현재 운영되는 공식 문서 URI 확인 |
| JCB 별도 개발자 문서 허브 | [JCB Global](https://www.global.jcb/en/) | 별도 공개 개발자 문서 허브를 확인하지 못함 | 현재 운영되는 공식 문서 URI 확인 |
| JCB YouTube | [공식 계정 안내](https://www.global.jcb/ja/policy/social-media/account.html) | 업데이트가 드물고 마케팅 비중이 높아 초기 목적 대비 저신호 | 기술 콘텐츠의 지속 발행 확인 |
| UnionPay Media Reports·Statements | [Media Center](https://www.unionpayintl.com/en/mediaCenter/) | JSON은 있으나 Media Reports는 외부 기사 재게시 성격이고 2025-03 이후 정체, Statements는 2017년 이후 정체 | 공식 1차 기술 자료가 지속 발행될 때 재검토 |
| 결제 네트워크 GitHub 조직 전체 | Visa·Mastercard·American Express 공식 조직 | 범용·비결제 저장소가 섞여 잡음이 큼. 선별한 Visa 저장소 6개 중 4개 release feed는 비어 있고 1개는 2022년 이후 정체 | 결제 관련 저장소별 활성 release 확인 |
| 검색 인덱스 기반 공식 페이지 발견 | 해당 없음 | 최신성·완전성과 재현성을 공식 출처가 보장하지 않음 | 사용하지 않음 |
| 브라우저 자동화 기반 목록 수집 | 해당 없음 | 렌더링·challenge 의존성과 운영 복잡도가 큼 | 사용하지 않음 |

2026-07-28 재검증에서 명시적으로 확인된 WAF 차단은 Mastercard 뉴스룸의 Akamai 403이다. Cloudflare 차단 출처는 이번 고정 범위에서 별도로 확인되지 않았지만 같은 원칙을 적용한다.

## 5. 변경 절차

1. 후보 URI를 일반 HTTP 클라이언트로 반복 조회한다.
2. 공식성, 접근 방식, 응답 형식과 필수 메타데이터를 기록한다.
3. adapter와 네트워크 없는 fixture 회귀 테스트를 추가한다.
4. 빈 목록, 파싱 실패, redirect와 allowlist 위반 시 이전 정상 상태 보존을 검증한다.
5. 실제 수집을 최소 두 번 실행해 두 번째 실행의 멱등성을 확인한다.
6. 이 문서와 Source Registry를 같은 변경에서 갱신한다.

차단·브라우저 의존으로 제외한 출처는 대체 경로를 추측하지 않는다. 공식적으로 제공되는 안정적인 feed나 API가 생긴 경우에만 새 후보로 등록한다.
