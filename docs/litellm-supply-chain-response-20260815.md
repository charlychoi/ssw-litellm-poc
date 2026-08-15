# LiteLLM 공급망 이슈 확인 및 조치 기록 — 2026-08-15

## 결론

CloudSEK와 Hudson Rock이 언급한 `litellm` PyPI 1.82.7/1.82.8 악성 패키지 이슈는 사실로 판단한다. 다만 “434,000개 파이프라인 비밀”이라는 표현은 보수적으로는 “약 434,000개 유출 파일/레코드 또는 잠재 노출 단위”로 해석해야 하며, Hudson Rock이 직접 확인한 수치는 153GB RAR, 433,909 files, 118,829 CI runner dumps, 2,488 corporate domains이다.

## 확인한 공개 근거

- Hudson Rock: `TeamPCP`가 Trivy CI/CD 경로를 거쳐 LiteLLM PyPI publishing token을 탈취했고, 1.82.7/1.82.8을 악성 버전으로 배포했다고 설명한다.
- Hudson Rock: 악성 `.pth` startup hook이 Python interpreter 초기화 시 실행되어 환경변수, `.kube/config`, `.aws/credentials` 등을 수집했다고 설명한다.
- Hudson Rock: 자체 분석 데이터셋을 153GB RAR / 433,909 files / 118,829 attributed CI runner dumps / 2,488 corporate domains로 제시한다.
- CloudSEK: 2,500+ companies 및 434,000 CI/CD pipelines 노출 가능성을 제시한 것으로 여러 공개 글과 Hudson Rock 글에서 인용된다.
- PyPI API 확인: 현재 PyPI `litellm` 공개 release 목록에는 1.82.0~1.82.6만 남아 있으며 1.82.7/1.82.8은 조회되지 않는다. 이는 악성 버전이 제거된 상태와 부합한다.

## 이 저장소 점검 결과

- `/opt/data/workspace/ssw-litellm-poc/pyproject.toml`은 기존에 `litellm[proxy]==1.83.7`을 사용하고 있었다.
- `/opt/data` 검색 결과, 이 환경의 requirements/pyproject/lock 파일에서 `1.82.7` 또는 `1.82.8` 사용 흔적은 발견하지 못했다.
- 시스템 Python에는 `litellm`이 설치되어 있지 않았다.
- 실행 중인 LiteLLM 프로세스나 LiteLLM Docker image는 발견하지 못했다.

## 적용한 조치

- `pyproject.toml`의 LiteLLM dependency를 `litellm[proxy]>=1.83.10,<2.0.0`으로 상향했다.
- `uv lock --upgrade-package litellm`을 실행하여 lockfile상 `litellm`을 1.96.2로 갱신했다.
- README 및 보안/운영 문서의 권장 버전을 `>=1.83.10` 기준으로 갱신했다.

## 운영 권고

1. 과거 CI 로그/캐시/runner image에서 `litellm==1.82.7` 또는 `litellm==1.82.8` 설치 이력이 있는지 확인한다.
2. 해당 기간에 실행된 runner가 있었다면 선택적으로가 아니라 runner에 노출된 cloud, GitHub, SSH, Kubernetes, AI provider key를 전부 회전한다.
3. CI에서는 `litellm[proxy]>=1.83.10,<2.0.0` 또는 검증된 최신 버전을 lockfile과 hash 기반으로 고정한다.
4. Trivy/GitHub Actions 등 보안 도구도 tag-only pin 대신 commit SHA pin을 검토한다.
5. `.pth` startup hook, `litellm_init.pth`, 비정상 systemd/sysmon 파일, 의심 Kubernetes pod를 IOC로 점검한다.

## Sources

- Hudson Rock, “Largest AI Supply Chain Breach of 2026: LiteLLM Hack Impacts Thousands of Global Enterprises – Claim Your Ethical Disclosure”, 2026-08-12.
- CloudSEK, “2,500+ Companies and 434,000 CI/CD Pipelines Exposed in the Largest AI Supply Chain Breach of 2026”, 2026-08-11.
- PyPI JSON API for `litellm` release metadata, checked 2026-08-15.
