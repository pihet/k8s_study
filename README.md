# Kubernetes & Cloud Native 데이터 엔지니어링 스터디 (k8s_study)

> **Minikube, Helm, kubectl**을 기반으로 로컬 쿠버네티스 환경에서 대용량 분산 데이터 파이프라인 컴포넌트(**Apache Kafka, Apache Spark, Apache Airflow 3, Kafka-UI**)를 구축하고 운영하는 실전 엔지니어링 가이드입니다.

---

## 1. 아키텍처 및 핵심 컴포넌트 구성

```
                 [Apache Airflow 3 (KubernetesExecutor)]
                          │ (배치 및 스트림 파이프라인 오케스트레이션)
                          v
[클라이언트 / 데이터 소스] ---> [Apache Kafka (Strimzi 3-Node HA)] ---> [Kafka-UI (8088)]
                                         │ (my-topic 파티션 스트림)
                                         v
                            [Apache Spark (Spark Operator)]
                             |- Driver Pod (1 Core, 1Gi)
                             `- Executor Pods (2대 분산 처리)
```

| 컴포넌트 | 배포 방식 | 네임스페이스 | 주요 역할 및 설명 |
| :--- | :--- | :--- | :--- |
| **Apache Kafka** | Strimzi Operator (CRD) | `kafka` | 3-브로커 고가용성(HA) 메시지 브로커 및 KRaft 컨트롤러 |
| **Kafka-UI** | Kubernetes Deployment | `kafka` | 카프카 브로커, 토픽, 컨슈머 그룹 모니터링 웹 대시보드 |
| **Apache Spark** | Spark Operator (CRD) | `spark` | Kubernetes 네이티브 분산 스트리밍 및 배치 데이터 처리 |
| **Apache Airflow 3** | Official Helm Chart | `airflow` | KubernetesExecutor 기반 분산 워크플로우 오케스트레이션 |

---

## 2. 사전 필수 도구 (Prerequisites)

- `kubectl` (v1.28+)
- `helm` (v3.12+)
- `minikube` (v1.32+)
- Docker Desktop 또는 Linux Docker Daemon

---

## 3. Minikube 클러스터 시작 및 최적화 설정

```bash
# 1. Minikube 클러스터 최적 사양 기동 (CPU 4 Core, Memory 8GB+)
minikube start --cpus=4 --memory=8192 --disk-size=30g --driver=docker

# 2. 클러스터 노드 상태 확인
kubectl get nodes
```

---

## 4. 컴포넌트별 배포 및 운영 가이드

### 4-1. Apache Kafka 배포 (`kafka/`)
- 상세 가이드: [kafka/README.md](kafka/README.md)

```bash
# 1. Strimzi Operator 설치
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm upgrade --install strimzi-kafka-operator strimzi/strimzi-kafka-operator -n kafka --create-namespace

# 2. Kafka HA 클러스터, 토픽, 보안 계정 배포
kubectl apply -f kafka/cluster/kafka-ha-cluster.yaml
kubectl apply -f kafka/topics/kafka-topic.yaml
kubectl apply -f kafka/users/app-user.yaml

# 3. Kafka-UI 웹 대시보드 배포
kubectl apply -f kafka-ui/kafka-ui.yaml
```

---

### 4-2. Apache Spark 배포 (`spark/`)
- 상세 가이드: [spark/README.md](spark/README.md)

```bash
# 1. Spark Operator 설치 및 RBAC 권한 구성
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update
helm upgrade --install spark-operator spark-operator/spark-operator \
  --namespace spark-operator --create-namespace --set webhook.enable=true

kubectl create serviceaccount spark -n spark --dry-run=client -o yaml | kubectl apply -f -
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=spark:spark --namespace=spark --dry-run=client -o yaml | kubectl apply -f -

# 2. PySpark Kafka 분산 처리 작업 제출
kubectl create configmap spark-kafka-code --from-file=spark/apps/spark_kafka_consumer.py -n spark --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f spark/apps/spark-kafka-job.yaml
```

---

### 4-3. Apache Airflow 3 배포 (`airflow/`)
- 상세 가이드: [airflow/README.md](airflow/README.md)

```bash
# 1. Apache Airflow 3 Helm 배포
helm repo add apache-airflow https://airflow.apache.org
helm repo update
helm upgrade --install airflow apache-airflow/airflow \
  --namespace airflow --create-namespace \
  -f airflow/values.yaml

# 2. DAG 파이프라인 CLI 트리거
kubectl exec -n airflow deployment/airflow-scheduler -c scheduler -- airflow dags trigger kafka_producer_pipeline
```

---

## 5. 포트포워딩 및 웹 대시보드 접속

```bash
# 1. Kafka-UI 포트포워딩
kubectl port-forward -n kafka svc/kafka-ui 8088:8080 &
# 접속 주소: http://localhost:8088

# 2. Airflow Webserver 포트포워딩
kubectl port-forward -n airflow svc/airflow-api-server 8080:8080 &
# 접속 주소: http://localhost:8080 (계정: admin / admin)

# 3. Kafka 브로커 로컬 포트포워딩 (CLI 테스트용)
kubectl port-forward -n kafka svc/my-cluster-kafka-bootstrap 9092:9092 &
```

---

## 6. 핵심 트러블슈팅 가이드

| 발생 에러 / 증상 | 원인 | 해결 명령어 |
| :--- | :--- | :--- |
| **Strimzi Operator CrashLoopBackOff** | 구버전 v1beta2 CRD 충돌 | `kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/1.1.0/strimzi-crds-1.1.0.yaml` |
| **Spark Driver 생성 거부 (Webhook Error)** | Mutating Webhook 미활성화 | `helm upgrade spark-operator ... --set webhook.enable=true` |
| **Airflow DAG UI 미노출** | DAG Processor 파싱 대기 | `kubectl logs -n airflow -l component=dag-processor --tail=30` 확인 |
| **Kafka SASL 인증 실패** | SCRAM 비밀번호 누락 | `kubectl get secret my-app-user -n kafka -o jsonpath='{.data.password}' \| base64 -d` 확인 |
