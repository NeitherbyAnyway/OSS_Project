# 기여 가이드

이 프로젝트는 GitHub Actions와 Python으로 협업 및 DORA 지표 자동화를 실습합니다. 작은 문서 개선부터 버그 수정까지 환영합니다.

## 시작하기

- Python 3.x와 Git이 필요합니다.
- 작업 전에 [README](README.md), [행동 강령](CODE_OF_CONDUCT.md), 관련 문서와 [ADR](docs/adr/)을 확인합니다.
- 큰 기능이나 동작 변경은 먼저 GitHub Issue 또는 Discussion에서 목적과 범위를 논의합니다.
- 자격 증명, 토큰, 개인 정보는 커밋하거나 로그에 기록하지 않습니다.

## 변경 작업

1. 작업 내용을 설명하는 Issue가 있으면 연결합니다.
2. `feature/<name>`, `fix/<name>`, `docs/<name>`처럼 목적이 분명한 브랜치에서 작업합니다.
3. 변경 범위를 좁게 유지하고, 동작이나 정책이 바뀌면 관련 문서를 함께 갱신합니다.
4. 제3자 코드나 자료를 추가할 때는 라이선스 호환성과 저작권 표시를 확인합니다.

## 로컬 검증

저장소 루트에서 다음 명령을 실행합니다.

```powershell
python -B .github/scripts/test_collect_dora_metrics.py
python -B .github/scripts/test_community_support.py
git diff --check
```

문서만 수정한 경우에는 `git diff --check`로 공백 오류를 확인하면 됩니다. 워크플로를 수정했다면 변경된 YAML과 Actions 권한·트리거도 검토합니다. 자동화는 Windows GitHub Actions에서 실행되므로 로컬 환경이 다르면 그 차이를 PR에 적습니다.

## Pull Request

- `main`을 대상으로 PR을 엽니다.
- PR 설명에 변경 이유, 주요 변경 사항, 실행한 검증을 기록하고 관련 Issue를 연결합니다.
- 리뷰 피드백에 응답하고 필요한 수정을 반영합니다.
- `main` 보호 규칙에 따라 쓰기 권한이 있는 리뷰어의 승인 1개 이상이 필요합니다. 작성자는 자신의 PR을 승인할 수 없습니다.
- 승인과 필수 검사를 확인한 뒤 병합합니다.

기여 내용은 별도 합의가 없는 한 이 저장소의 [MIT License](LICENSE)에 따라 배포할 수 있어야 합니다.
