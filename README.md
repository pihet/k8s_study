# 🚀 Kubernetes & Cloud Native 스터디 (k8s_study)

> **kubectl, Helm, Minikube**를 활용한 로컬 쿠버네티스 클러스터 구축부터 실전 데이터 엔지니어링 파이프라인(Kafka, Spark/Flink, Airflow) 애플리케이션 배포 및 트러블슈팅까지 100% 재현 가능한 올인원 가이드입니다.

---

## 📌 목차 (Table of Contents)
1. [사전 필수 도구 설치 (Prerequisites)](#1-사전-필수-도구-설치-prerequisites)
   - [1-1. Windows 환경 (winget / choco)](#1-1-windows-환경-powershell--winget-기준)
   - [1-2. WSL2 / Linux 환경](#1-2-wsl2--linux-환경-ubuntudebian-기준)
   - [1-3. macOS 환경](#1-3-macos-환경-homebrew-기준)
   - [1-4. 설치 검증](#1-4-설치-검증)
2. [Minikube 클러스터 시작 및 최적화 설정](#2-minikube-클러스터-시작-및-최적화-설정)
   - [2-1. 사양 최적화 클러스터 기동](#2-1-사양-최적화-클러스터-기동-권장-노트북-사양)
   - [2-2. kubectl 컨텍스트 및 노드 상태 확인](#2-2-kubectl-컨텍스트-및-노드-상태-확인)
   - [2-3. 필수 Minikube 애드온 활성화](#2-3-필수-minikube-애드온-활성화)
3. [kubectl 기본 사용법 및 클러스터 동작 검증](#3-kubectl-기본-사용법-및-클러스터-동작-검증)
4. [Helm 기본 개념 및 패키지 관리 가이드](#4-helm-기본-개념-및-패키지-관리-가이드)
5. [실전 컴포넌트 배포 시나리오 (MariaDB, Kafka, Flink/Spark, Airflow)](#5-실전-컴포넌트-배포-시나리오)
6. [외부 서비스 접속 및 포트포워딩 가이드](#6-외부-서비스-접속-및-포트포워딩-가이드)
7. [트러블슈팅 및 Minikube 클린 리셋 가이드](#7-트러블슈팅-및-minikube-클린-리셋-가이드)
8. [학습 및 페어 프로그래밍 가이드](#8-학습-및-페어-프로그래밍-가이드)

---

## 1. 사전 필수 도구 설치 (Prerequisites)

쿠버네티스를 로컬에서 다루기 위한 **3대 필수 CLI 도구 (`kubectl`, `helm`, `minikube`)**를 설치합니다.

### 1-1. Windows 환경 (PowerShell / winget 기준)
> **💡 필수 선행 조건**: Windows 환경에서는 **Docker Desktop**이 설치되어 실행 중이거나 **Hyper-V** 기능이 활성화되어 있어야 합니다.

```powershell
# 1. kubectl 설치
winget install Kubernetes.kubectl
# (대안) choco install kubernetes-cli

# 2. Helm 설치
winget install Helm.Helm
# (대안) choco install kubernetes-helm

# 3. Minikube 설치
winget install Kubernetes.minikube
# (대안) choco install minikube
```

### 1-2. WSL2 / Linux 환경 (Ubuntu/Debian 기준)
```bash
# 1. kubectl 설치
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update && sudo apt-get install -y kubectl

# 2. Helm 설치
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 3. Minikube 설치
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

### 1-3. macOS 환경 (Homebrew 기준)
```bash
brew install kubectl
brew install helm
brew install minikube
```

### 1-4. 설치 검증
새 터미널 창을 열고 각 도구의 버전이 정상 출력되는지 확인합니다:
```bash
kubectl version --client
helm version
minikube version
```

---

## 2. Minikube 클러스터 시작 및 최적화 설정

### 2-1. 사양 최적화 클러스터 기동 (권장 노트북 사양)
스트리밍 엔진(Kafka, Flink/Spark) 및 워크플로우 도구(Airflow) 등 대규모 데이터 파이프라인 컴포넌트들을 안정적으로 구동하기 위해 **노트북 사양(8 Cores / 16 Threads, 32GB RAM)** 에 맞춘 리소스를 할당합니다.

```bash
# Docker 드라이버 기준 (가장 안정적 / 권장)
minikube start \
  --driver=docker \
  --cpus=8 \
  --memory=16384 \
  --disk-size=50g

# (참고 1) Hyper-V 드라이버를 사용할 경우:
# minikube start --driver=hyperv --cpus=8 --memory=16384 --disk-size=50g --no-vtx-check

# (참고 2) 가벼운 실습용 기본 사양:
# minikube start --cpus=4 --memory=8192 --disk-size=30g
```

### 2-2. kubectl 컨텍스트 및 노드 상태 확인
```bash
# 1. 현재 컨텍스트가 minikube인지 확인
kubectl config current-context

# 2. 노드 상태 확인 (STATUS가 Ready여야 함)
kubectl get nodes
```

### 2-3. 필수 Minikube 애드온 활성화
```bash
# 1. 동적 스토리지 프로비저닝 (기본 활성화되어 있으나 확인)
minikube addons enable storage-provisioner
minikube addons enable default-storageclass

# 2. 리소스 모니터링 (kubectl top node/pod 지원)
minikube addons enable metrics-server

# 3. 인그레스 컨트롤러 (HTTP 트래픽 라우팅)
minikube addons enable ingress

# 4. 웹 기반 GUI 대시보드 (선택 사항)
minikube addons enable dashboard
```

---

## 3. kubectl 기본 사용법 및 클러스터 동작 검증

클러스터가 정상 동작하는지 테스트용 Nginx 웹 서버를 배포하여 검증합니다.

```bash
# 1. 테스트 네임스페이스 생성
kubectl create namespace test

# 2. Nginx Deployment 생성
kubectl create deployment test-nginx --image=nginx:alpine -n test

# 3. Pod 실행 대기
kubectl wait --for=condition=Ready pod -l app=test-nginx -n test --timeout=60s

# 4. Service 노출 (NodePort)
kubectl expose deployment test-nginx --port=80 --type=NodePort -n test

# 5. Pod 및 Service 상태 조회
kubectl get pod,svc -n test

# 6. 테스트 리소스 정리
kubectl delete namespace test
```

---

## 4. Helm 기본 개념 및 패키지 관리 가이드

Helm은 쿠버네티스의 패키지 관리자(Package Manager)입니다. 복잡한 다중 YAML 파일을 하나의 차트(Chart)로 묶어 설치, 업그레이드, 롤백을 손쉽게 수행할 수 있습니다.

### 주요 Helm 명령어 모음
```bash
# 1. 저장소(Repository) 추가 및 갱신
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 2. 차트 검색
helm search repo bitnami/redis

# 3. 기본 설정값(values.yaml) 확인
helm show values bitnami/redis > custom_values.yaml

# 4. 커스텀 설정을 적용하여 차트 설치
helm install my-redis bitnami/redis -n test --create-namespace -f custom_values.yaml

# 5. 설치된 릴리스 목록 조회
helm list -A

# 6. 차트 업그레이드
helm upgrade my-redis bitnami/redis -n test -f updated_values.yaml

# 7. 차트 삭제
helm delete my-redis -n test
```

---

## 5. 실전 컴포넌트 배포 시나리오

BIDA 플랫폼 및 대규모 데이터 인프라 실습을 위한 주요 컴포넌트 배포 순서입니다.

```
┌──────────────────┐      ┌──────────────────────────┐      ┌───────────────────────────┐
│ 1. MariaDB       │ ───► │ 2. Strimzi Apache Kafka  │ ───► │ 3. Apache Flink / Spark   │
│ (RDBMS / Secret) │      │ (Kafka Cluster & Topics) │      │ (Streaming & Batch Proc)  │
└──────────────────┘      └──────────────────────────┘      └───────────────────────────┘
                                                                          │
                                                                          ▼
                                                            ┌───────────────────────────┐
                                                            │ 4. Apache Airflow         │
                                                            │ (Orchestration & DAGs)    │
                                                            └───────────────────────────┘
```

### [Step 1] MariaDB 배포
```bash
# 1. 네임스페이스 및 Secret 생성
kubectl create namespace mariadb
kubectl create secret generic mariadb-secret \
  --from-literal=MYSQL_ROOT_PASSWORD=rootpassword \
  --from-literal=MYSQL_DATABASE=study_db \
  --from-literal=MYSQL_USER=admin \
  --from-literal=MYSQL_PASSWORD=adminpassword \
  -n mariadb

# 2. MariaDB 배포 (StatefulSet / PV)
kubectl apply -f maria_pv.yaml -n mariadb
kubectl apply -f mariadb.yaml -n mariadb
```

### [Step 2] Apache Kafka 배포 (Strimzi Operator)
> 👉 **상세 가이드 및 트러블슈팅**: [📖 `kafka/README.md`](./kafka/README.md) 참조

```bash
# 1. Strimzi 최신 CRD 수동 적용 (v1 지원)
kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/1.1.0/strimzi-crds-1.1.0.yaml

# 2. Strimzi Operator 설치 (Helm)
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm install strimzi-operator strimzi/strimzi-kafka-operator --namespace kafka --create-namespace

# 3. Kafka 클러스터 배포 (KRaft 모드)
kubectl apply -f kafka/kafka-cluster.yaml
```

### [Step 3] Apache Flink / Spark 클러스터 배포
```bash
# 1. cert-manager 및 Flink Operator 설치
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.18.2/cert-manager.yaml --insecure-skip-tls-verify

helm repo add flink-operator-repo https://downloads.apache.org/flink/flink-kubernetes-operator-1.13.0/
helm repo update
helm install flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator \
  -n flink-kubernetes-operator \
  --create-namespace \
  --insecure-skip-tls-verify

# 2. Flink Session Cluster & SQL Gateway 매니페스트 적용
kubectl create namespace flink
kubectl apply -f flink-session-cluster.yaml -n flink
kubectl apply -f flink-sql-gateway.yaml -n flink
```

### [Step 4] Apache Airflow 배포 (Helm)
```bash
# 1. Airflow Helm Repo 추가
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# 2. Airflow 설치 (네임스페이스: airflow)
kubectl create namespace airflow
helm install airflow apache-airflow/airflow -n airflow -f values.yaml

# 3. Admin 관리자 계정 생성
kubectl exec -n airflow deploy/airflow-scheduler -c scheduler -- \
  airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

---

## 6. 외부 서비스 접속 및 포트포워딩 가이드

로컬 환경(PC 브라우저)에서 각 서비스의 웹 UI에 접근하려면 별도의 터미널에서 아래 명령을 실행합니다:

| 서비스 | 포트포워딩 명령어 | 웹 브라우저 URL | 기본 접속 계정 |
| :--- | :--- | :--- | :--- |
| **Airflow UI** | `kubectl port-forward -n airflow svc/airflow-webserver 8080:8080` | `http://localhost:8080` | `admin` / `admin` |
| **Flink Dashboard** | `kubectl port-forward -n flink svc/flink-rest 8081:8081` | `http://localhost:8081` | (로그인 없음) |
| **MariaDB** | `kubectl port-forward -n mariadb svc/mariadb-service 3306:3306` | `localhost:3306` | `admin` / `adminpassword` |
| **Minikube Dashboard**| `minikube dashboard` | (자동으로 브라우저 기동) | (로그인 없음) |

---

## 7. 트러블슈팅 및 Minikube 클린 리셋 가이드

### 7-1. Minikube 클러스터 멈춤 또는 VM 깨짐 시 완전 초기화 (Windows PowerShell)
```powershell
# 1. minikube 프로세스 강제 종료
taskkill /IM minikube.exe /F 2>$null

# 2. Hyper-V 사용 시 VM 강제 중지 및 삭제
Stop-VM -Name minikube -TurnOff -Force 2>$null
Remove-VM -Name minikube -Force 2>$null

# 3. Minikube 전체 캐시 및 설정 완전 제거
minikube delete --all --purge
Remove-Item -Recurse -Force "$env:USERPROFILE\.minikube\machines\minikube" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\.minikube\profiles\minikube" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.minikube\config\config.json" -ErrorAction SilentlyContinue

# 4. 클러스터 재시작
minikube start --driver=docker --cpus=8 --memory=16384 --disk-size=50g
```

### 7-2. Flink Deployment 종료 시 지워지지 않고 멈춰있을 때 (Finalizer 강제 해제)
```bash
kubectl patch flinkdeployment -n flink -p '{"metadata": {"finalizers": null}}' --type merge
```

### 7-3. Helm 리소스 및 전체 네임스페이스 일괄 정리
```bash
# 전체 Helm 릴리스 확인 후 삭제
helm list -A
helm delete airflow -n airflow
helm delete flink-kubernetes-operator -n flink-kubernetes-operator
helm delete my-strimzi-kafka-operator -n kafka-kubernetes-operator

# 네임스페이스 삭제
kubectl delete namespace airflow flink flink-kubernetes-operator kafka-kubernetes-operator mariadb
```

---

## 8. 학습 및 페어 프로그래밍 가이드
- 본 프로젝트는 단계별 직접 실습 및 트러블슈팅 체득을 최우선으로 합니다.
- 가이드라인 및 프롬프트 규칙: [`AGENTS.md`](./AGENTS.md)
