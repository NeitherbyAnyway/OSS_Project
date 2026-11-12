# 기여 가이드

## 브랜치 작업

1. `main` 브랜치의 최신 변경사항을 가져옵니다.
2. 작업 목적이 드러나는 feature 브랜치를 만듭니다.
   - 예: `feature/add-report-export`
   - 버그 수정 예: `feature/fix-report-date`
3. 변경사항은 하나의 목적에 집중해 작업합니다.

## Conventional Commits

커밋 메시지는 다음 형식을 사용합니다.

```text
<type>(<scope>): <summary>
```

`scope`는 필요할 때 사용하고, 요약은 간결하게 작성합니다. 주요 type은 다음과 같습니다.

- `feat`: 사용자 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `test`: 테스트 추가 또는 수정
- `refactor`: 동작 변경 없는 코드 개선
- `chore`: 빌드, 도구, 기타 유지보수

예시:

```text
docs: add contribution workflow
feat(metrics): export weekly summary
fix(report): handle empty release list
```

## Pull Request

1. feature 브랜치를 원격 저장소에 push하고 `main`을 대상으로 PR을 엽니다.
2. PR 제목은 변경 목적을 설명하고, 본문에는 변경 내용과 검증 방법을 적습니다.
3. 관련 검토를 마치고 피드백을 반영한 뒤 저장소의 머지 규칙에 따라 병합합니다.
