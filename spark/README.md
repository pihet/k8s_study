# Apache Spark on Kubernetes 운영 가이드

> Spark Operator 기반으로 Kubernetes 클러스터 상에서 PySpark 스트리밍 및 배치 분산 작업을 실행하는 가이드입니다.

---

## 1. 주요 파일별 역할 및 기능

- [`apps/spark_kafka_consumer.py`](./apps/spark_kafka_consumer.py): Kafka 브로커의 `my-topic` 스트림 데이터를 구독하여 실시간 분산 집계 및 처리하는 PySpark 애플리케이션.
- [`apps/spark-kafka-job.yaml`](./apps/spark-kafka-job.yaml): SparkApplication CRD를 통해 Driver(1 Core)와 Executor(2대) 파드를 자동 생성/스케줄링하는 Kubernetes 매니페스트.

---

## 2. 인프라 배포 및 실행 명령어

```bash
# 1. Spark Operator 설치 및 RBAC 권한 구성
helm upgrade --install spark-operator spark-operator/spark-operator \
  --namespace spark-operator --create-namespace --set webhook.enable=true
kubectl create serviceaccount spark -n spark --dry-run=client -o yaml | kubectl apply -f -
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=spark:spark --namespace=spark --dry-run=client -o yaml | kubectl apply -f -

# 2. PySpark 코드를 ConfigMap으로 클러스터에 등록
kubectl create configmap spark-kafka-code --from-file=spark/apps/spark_kafka_consumer.py -n spark --dry-run=client -o yaml | kubectl apply -f -

# 3. SparkApplication 분산 작업 제출 및 모니터링
kubectl apply -f spark/apps/spark-kafka-job.yaml
kubectl get sparkapplications -n spark -w

# 4. Spark Driver 로그 확인
kubectl logs -n spark -l spark-role=driver -f
```

---

## 3. 핵심 에러 발생 시 해결법 (Troubleshooting)

- **에러 1: `Spark Operator Mutating Webhook Connection Refused`**
  - **원인**: Spark Operator 파드의 웹훅 포트(9443)가 준비되지 않았거나 웹훅 설정이 비활성화됨.
  - **해결**: Helm 설치 시 `--set webhook.enable=true` 옵션을 명시하고 `spark-operator` 네임스페이스의 컨트롤러/웹훅 파드 상태 확인:
    ```bash
    kubectl get pods -n spark-operator
    ```
- **에러 2: `Driver 파드가 Executor 파드를 생성하지 못함 (Permission Denied)`**
  - **원인**: `spark` 서비스 어카운트에 파드 생성 클러스터 롤(ClusterRole) 권한이 바인딩되지 않음.
  - **해결**: `edit` 롤을 `spark:spark` 서비스 어카운트에 바인딩:
    ```bash
    kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=spark:spark --namespace=spark
    ```
