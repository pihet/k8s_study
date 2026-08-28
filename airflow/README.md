# Apache Airflow 3 on Kubernetes 운영 가이드

> KubernetesExecutor 기반으로 파이프라인 태스크마다 독립적인 Kubernetes Pod를 동적 생성하여 분산 실행하는 Airflow 3 가이드입니다.

---

## 1. 주요 파일별 역할 및 기능

- [`dags/kafka_producer_pipeline.py`](./dags/kafka_producer_pipeline.py): Kafka 브로커로 데이터 이벤트를 주기적으로 자동 발행하는 Airflow 파이프라인.
- [`dags/shipyard_master_planning_dag.py`](./dags/shipyard_master_planning_dag.py): 대규모 데이터 처리 및 분산 집계를 수행하는 정기 배치 파이프라인.
- [`dags/shipyard_mlops_continuous_training_dag.py`](./dags/shipyard_mlops_continuous_training_dag.py): 데이터 드리프트 감지 및 자동 재학습 워크플로우를 관제하는 Continuous Training 파이프라인.
- [`values.yaml`](./values.yaml): KubernetesExecutor, PostgreSQL 백엔드 DB, Git-Sync 주기 및 리소스 제한이 정의된 Airflow 3 Helm 설정 파일.

---

## 2. 인프라 배포 및 실행 명령어

```bash
# 1. Apache Airflow 3 Helm 배포
helm repo add apache-airflow https://airflow.apache.org
helm repo update
helm upgrade --install airflow apache-airflow/airflow \
  --namespace airflow --create-namespace \
  -f airflow/values.yaml

# 2. 파드 기동 상태 확인
kubectl get pods -n airflow

# 3. DAG 목록 확인 및 수동 실행 (CLI)
kubectl exec -n airflow deployment/airflow-scheduler -c scheduler -- airflow dags list
kubectl exec -n airflow deployment/airflow-scheduler -c scheduler -- airflow dags trigger kafka_producer_pipeline

# 4. Airflow Webserver 포트포워딩
kubectl port-forward -n airflow svc/airflow-api-server 8080:8080
# 접속 주소: http://localhost:8080 (계정: admin / admin)
```

---

## 3. 핵심 에러 발생 시 해결법 (Troubleshooting)

- **에러 1: `신규 DAG 파일 추가 후 Airflow 웹 UI에 표시되지 않음`**
  - **원인**: Airflow 3의 DAG Processor가 번들 새로고침 주기(Bundle Refresh Interval)에 따라 비동기로 파싱함.
  - **해결**: DAG Processor 로그를 확인하여 파일 파싱 에러 여부 점검:
    ```bash
    kubectl logs -n airflow -l component=dag-processor --tail=40
    ```
- **에러 2: `Worker Pod가 Pending 상태로 멈춰 있음`**
  - **원인**: 클러스터 노드 메모리/CPU 자원 부족 또는 PersistentVolume 마운트 대기.
  - **해결**: `kubectl describe pod -n airflow <POD_NAME>`로 이벤트 확인 및 리소스 정리.
