# 저장소 작업 지침

- 저장소 소개와 주간 처리량 설명은 [README.md](README.md)를, 자동화 동작은 [.github/workflows/throughput.yml](.github/workflows/throughput.yml)을 기준으로 확인합니다.
- 주간 처리량 워크플로는 Windows의 GitHub Actions에서 PowerShell로 실행되며, 매주 일요일 00:00 UTC 또는 수동 실행으로 최근 7일 동안 닫힌 이슈 수를 Actions 요약에 기록합니다. 동작을 바꿀 때 스케줄, 수동 실행, 집계 기간, 출력 요약을 함께 고려합니다.
- 현재 워크플로는 `GH_TOKEN` 환경 변수에 저장소 Secret `GH_TOKEN`을 전달합니다. 토큰 값을 코드나 로그에 노출하지 말고, 필요한 최소 권한만 유지합니다. 비밀 설정이 바뀌면 README도 함께 갱신합니다.
- README에는 빌드나 테스트 명령이 정의되어 있지 않습니다. 검증 도구를 임의로 전제하지 말고, 워크플로를 수정했다면 가능한 경우 YAML/Actions 검사를 수행하고 `git diff --check`도 확인합니다.
- README의 `C` 사전 요구사항만으로 현재 저장소에 C 빌드 체계가 있다고 가정하지 않습니다. 언어나 도구 선택은 실제 소스와 설정 파일을 확인합니다.