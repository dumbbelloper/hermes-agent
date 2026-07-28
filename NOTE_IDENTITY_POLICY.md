# 수집 문서 식별과 멱등성 정책

> 기준일: 2026-07-28
>
> 상태: 적용

이 문서는 Hermes Agent와 향후 Writer Skill이 같은 공식 자료를 하루에 여러 번 처리해도 중복 문서를 만들지 않고, 원문 변경과 사람의 수정을 안전하게 구분하기 위한 기준이다.

## 1. 식별자

### `record_id`

하나의 수집 레코드를 식별하는 불변 기본키다.

```text
SHA-256(source_id + "\n" + canonical_url)
```

- `source_id`는 [Source Registry](./Automation/config/sources.json)의 고정 ID다.
- `canonical_url`은 tracking query, fragment와 불필요한 trailing slash를 제거한 공식 URL이다.
- 같은 출처에서 같은 URL을 다시 수집하면 항상 같은 `record_id`가 생성된다.
- 서로 다른 출처가 같은 사건을 발표하면 별도 레코드로 유지한다. 사건 단위 중복 통합은 별도 기능이다.

### `source_fingerprint`

`discovered_at`을 제외한 정규화 수집 레코드 전체의 SHA-256이다. 제목, 게시일, 설명과 외부 ID 등이 변경되면 값이 달라진다.

`record_id`는 “같은 자료인가”, `source_fingerprint`는 “수집된 내용이 달라졌는가”를 판단한다.

## 2. 필수 Frontmatter

Writer가 생성하거나 관리하는 Inbox·Notes 문서는 다음 필드를 가져야 한다.

| 필드 | 역할 |
| --- | --- |
| `note_schema_version` | 문서 메타데이터 schema 버전 |
| `record_id` | 수집 레코드 기본키 |
| `source_fingerprint` | 마지막으로 확인한 수집 레코드 상태 |
| `source_id` | Source Registry 출처 ID |
| `canonical_url` | 정규화된 공식 URL |
| `created_by` | `manual` 또는 `hermes-agent` |
| `status` | `draft`, `reviewed`, `update_pending` 등 검토 상태 |

`generator`, `generator_version`, `first_collected_at`과 `last_checked_at`도 감사와 재현을 위해 함께 기록한다.

## 3. Writer 판정

| 조건 | 판정 | 동작 |
| --- | --- | --- |
| Vault에 `record_id` 없음 | `create` | 새 Inbox 문서 생성 |
| 같은 `record_id`, 같은 fingerprint | `skip` | 파일을 수정하지 않음 |
| 같은 `record_id`, 다른 fingerprint | `update_pending` | 기존 파일을 덮어쓰지 않고 검토 대기 |
| 같은 `record_id`가 여러 문서에 존재 | 오류 | 자동 작성을 중단하고 중복 해소 |
| `record_id`가 source와 URL에서 계산한 값과 다름 | 오류 | 자동 작성을 중단하고 메타데이터 수정 |

`created_by: manual` 문서는 항상 사람이 소유한 본문으로 취급한다. 향후 자동 생성 문서도 사람이 수정할 수 있으므로 Writer는 기존 본문을 무조건 덮어쓰지 않는다.

## 4. 인덱스 운영

Vault 인덱스는 `Inbox/`와 `Notes/`의 Frontmatter를 실행 시점에 읽어 메모리에서 재구성한다. 별도의 영구 index 파일을 기준 데이터로 사용하지 않으므로 cache 유실이나 여러 환경 사이의 stale 상태가 문서 중복을 만들지 않는다.

검증:

```bash
PYTHONPATH=Automation/src python3 -m hermes_agent validate-notes \
  --vault-dir .
```

Writer 판정:

```bash
PYTHONPATH=Automation/src python3 -m hermes_agent note-status \
  --vault-dir . \
  --record-id <record-id> \
  --source-fingerprint <source-fingerprint>
```

Writer Skill은 한 실행에서 Vault를 한 번 scan하고 여러 레코드의 판정을 같은 인덱스로 처리한다. 실제 파일 생성은 판정 결과가 `create`인 경우에만 수행한다.

## 5. 변경과 충돌 처리

- 원문 메타데이터가 변경되면 기존 문서의 `status`를 `update_pending`으로 바꾸는 기능을 후속 구현한다.
- 자동 갱신을 도입할 때도 사람이 작성한 요약과 해석은 managed block과 분리하기 전까지 덮어쓰지 않는다.
- `source_id` 변경이나 공식 URL 이전으로 `record_id`가 바뀌는 경우 이전 ID를 alias로 보존하는 migration 절차가 필요하다.
- 동일 사건의 여러 조직 발표를 하나로 묶는 event key는 `record_id`와 분리해 설계한다.
