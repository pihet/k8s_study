# 🌪️ Apache Airflow on Kubernetes 빠른 시작 가이드 (setting.md)

이 문서는 처음 시작하는 사람도 **위에서부터 순서대로 명령어를 복사해서 터미널에 붙여넣기만 하면 100% 동일하게 동작**하도록 작성된 실전 구축 가이드입니다.

---

## 📋 0. 사전 준비 (Minikube 기동)

```bash
# Minikube 클러스터 기동
minikube start --driver=docker --cpus=6 --memory=12288
```

---

## 🛠️ Step 1. 공식 Helm 저장소 등록

```bash
# 1. 아파치 에어플로우 공식 레포지토리 추가
helm repo add apache-airflow https://airflow.apache.org

# 2. 최신 차트 목록 업데이트
helm repo update
```

---

## 📝 Step 2. 로컬 최적화 `values.yaml` 생성

Airflow를 가볍고 강력한 **`KubernetesExecutor`**로 돌리기 위한 설정 파일을 생성합니다.

```bash
# airflow 폴더로 이동
cd ~/workspace/k8s_study/airflow
```

`airflow/values.yaml` 파일을 생성하고 아래 내용을 저장합니다:

```yaml
# airflow/values.yaml

# 1. 실행 엔진: KubernetesExecutor (태스크마다 K8s 파드를 동적으로 띄워 실행 ⭐)
executor: "KubernetesExecutor"

# 2. 불필요한 데몬 비활성화 (메모리 절약)
triggerer:
  enabled: false
statsd:
  enabled: false

# 3. 웹서버 설정 (Admin 로그인 계정 자동 생성)
webserver:
  replicas: 1
  defaultUser:
    enabled: true
    role: Admin
    username: admin
    password: admin
    email: admin@example.com
    firstName: Admin
    lastName: User

# 4. 스케줄러 1대
scheduler:
  replicas: 1

# 5. 메타데이터 DB (PostgreSQL 5Gi 영구 디스크)
postgresql:
  enabled: true
  persistence:
    size: 5Gi

# 6. 파이썬 DAG 파일 저장용 영구 볼륨 (1Gi PVC)
dags:
  persistence:
    enabled: true
    size: 1Gi
    storageClassName: standard
```

---

## 🚀 Step 3. Airflow 클러스터 배포

```bash
# airflow 네임스페이스에 Helm 배포 실행
helm install airflow apache-airflow/airflow --namespace airflow --create-namespace -f values.yaml
```

---

## ⏳ Step 4. 배포 완료 확인 및 웹 UI 접속

```bash
# 1. 파드 기동 상태 실시간 관찰 (약 1~2분 소요, 모두 Running 될 때까지 대기)
kubectl get pods -n airflow -w
```

> **정상 파드 목록 예시:**
> - `airflow-postgresql-0` (1/1 Running)
> - `airflow-scheduler-xxxx` (2/2 Running)
> - `airflow-api-server-xxxx` (또는 webserver) (1/1 Running)
> - `airflow-dag-processor-xxxx` (2/2 Running)

### 🌐 웹 브라우저 접속 (포트포워딩)
```bash
# Airflow 웹 UI 포트포워딩 실행 (8081 포트로 실행)
kubectl port-forward -n airflow svc/airflow-api-server 8081:8080
```
> 🌐 **웹 접속:** 브라우저에서 [`http://localhost:8081`](http://localhost:8081) 접속  
> 🔑 **로그인:** ID: **`admin`** / PW: **`admin`**

---

## 📜 Step 5. 첫 번째 파이썬 DAG 작성 & 전달

`airflow/dags/` 폴더에 샘플 DAG 코드를 작성합니다.

```python
# airflow/dags/hello_k8s_dag.py
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'pihet',
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'hello_kubernetes_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['study', 'k8s'],
) as dag:

    t1 = BashOperator(
        task_id='print_start',
        bash_command='echo "Airflow on K8s Pipeline Started!"',
    )

    t2 = BashOperator(
        task_id='print_date',
        bash_command='date',
    )

    t1 >> t2
```

### 📂 DAG 파일을 Airflow 파드로 복사하기
```bash
# 로컬 dags 폴더의 파이썬 파일을 Airflow 파드의 dags 디렉토리로 동기화
kubectl cp dags/hello_k8s_dag.py airflow/$(kubectl get pod -n airflow -l component=scheduler -o jsonpath='{.items[0].metadata.name}'):/opt/airflow/dags/
```

---

## 🎯 Step 6. DAG 실행 & KubernetesExecutor 일꾼 파드 관찰

1. Airflow 웹 UI([`http://localhost:8081`](http://localhost:8081))에서 **`hello_kubernetes_dag`**를 활성화(토글 ON)하고 **`Trigger DAG` (▶ 재생 버튼)**을 클릭합니다.
2. 터미널 또는 OpenLens에서 `kubectl get pods -n airflow -w`를 보면:
   - 태스크가 실행되는 순간 **`hello-kubernetes-dag-print-start-xxxx`** 라는 일꾼 파드가 동적으로 생성되어 작업을 수행하고,
   - 작업 완료 후 파드가 자동으로 정리(`Completed`)되는 **`KubernetesExecutor`의 진가**를 직접 확인할 수 있습니다!
