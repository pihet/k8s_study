# Kubernetes & Cloud Native 데이터 엔지니어링 스터디 (k8s_study)

> **kubectl, Helm, Minikube**를 활용한 로컬 쿠버네티스 클러스터 구축부터 실전 데이터 엔지니어링 파이프라인(Kafka, Flink, Spark, Airflow, MLflow, MinIO) 마이크로서비스 배포 및 MLOps 자동화 가이드입니다.

---

## 1. 사전 필수 도구 (Prerequisites)

- `kubectl`, `helm`, `minikube`
- Python 3.11+ / Docker Desktop 또는 Linux KVM

---

## 2. Minikube 클러스터 시작 및 최적화 설정

```bash
# Minikube 최적 사양 클러스터 기동 (CPU 4 Core, Memory 8GB+)
minikube start --cpus=4 --memory=8192 --disk-size=30g --driver=docker

# 노드 및 시스템 상태 확인
kubectl get nodes
```

---

## 3. 핵심 배포 파이프라인 매니페스트 및 컴포넌트

1. **Apache Kafka (Strimzi Operator HA)**: [kafka/](kafka/)
2. **Apache Flink 스트리밍 엔진**: [flink/](flink/)
3. **Apache Airflow 3 오케스트레이션**: [airflow/](airflow/)
4. **Apache Spark 분산 데이터 레이크하우스**: [spark/](spark/)
5. **Kafka UI 모니터링 대시보드**: [kafka-ui/](kafka-ui/)

---

## 4. 원클릭 통합 포트포워딩 가이드

2차 프로젝트 디렉토리의 통합 스크립트를 통해 모든 서비스를 로컬 포트로 연결합니다:

```bash
# 9대 마이크로서비스 일괄 포트포워딩
pfall

# 개별 서비스 접속 주소
# - React Frontend : http://localhost:3000
# - FastAPI Docs   : http://localhost:8000/docs
# - MLflow UI      : http://localhost:5000
# - Flink UI       : http://localhost:8082
# - Airflow Web    : http://localhost:8080 (admin / admin)
# - Kafka UI       : http://localhost:8088
# - MinIO Console  : http://localhost:9001 (minioadmin / minioadmin123)
```

---

## 5. 조선소 스마트 스케줄링 프로젝트 연동

실제 872개 블록 및 66개 정반 MLOps 디지털 트윈 플랫폼 코드는 `../samsung_project/2차프로젝트`에 위치하며, `pj2` 명령어로 즉시 가상환경과 함께 전환할 수 있습니다.
