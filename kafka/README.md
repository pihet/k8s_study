# Apache Kafka on Kubernetes (Strimzi Operator)

Kubernetes 환경에서 **Strimzi Kafka Operator**를 사용하여 Apache Kafka(KRaft 모드)를 구축하고 운영하는 실습 및 트러블슈팅 정리입니다.

---

## 📑 목차
1. [Strimzi Operator 및 Kafka 버전 선택](#1-strimzi-operator-및-kafka-버전-선택)
2. [설치 및 배포 가이드](#2-설치-및-배포-가이드)
3. [🔥 트러블슈팅 케이스: CRD 버전 불일치로 인한 CrashLoopBackOff](#3--트러블슈팅-케이스-crd-버전-불일치로-인한-crashloopbackoff)
4. [주요 학습 포인트](#4-주요-학습-포인트)

---

## 1. Strimzi Operator 및 Kafka 버전 선택

### 1) Strimzi 1.1.0 지원 버전
- **Apache Kafka 4.3.0** (신규 배포 시 최우선 권장)
- **Apache Kafka 4.2.1** (4.2.x 호환성 유지 필요 시 권장)
- **Apache Kafka 4.2.0** (4.2.1 패치가 존재하므로 비권장)
- *(참고: 4.1.x는 Strimzi 1.1.0부터 지원 제외)*

### 2) Kafka 4.x의 주요 변화
- **ZooKeeper 완전 제거 & KRaft 전용**: Kafka 4.x부터는 ZooKeeper 없이 **KRaft(Kafka Raft Metadata Mode)**로만 동작합니다.
- **`KafkaNodePool` 도입**: Broker 및 Controller 역할을 정의하기 위해 `KafkaNodePool` 리소스를 필수로 사용합니다.
- **Strimzi CRD v1 적용**: Strimzi 1.0.0 이후부터 기존 `v1beta2` 등이 폐기되고 `apiVersion: kafka.strimzi.io/v1`만 지원됩니다.

---

## 2. 설치 및 배포 가이드

### 1단계: Strimzi Helm 저장소 추가 및 네임스페이스 생성
```bash
# Helm 저장소 추가 및 업데이트
helm repo add strimzi https://strimzi.io/charts/
helm repo update

# kafka 네임스페이스 생성
kubectl create namespace kafka
```

### 2단계: 최신 CRD 수동 적용 (중요!)
> ⚠️ **주의**: Helm은 기존 클러스터에 설치된 CRD를 자동으로 업그레이드해주지 않으므로, CRD를 직접 최신화합니다.

```bash
kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/1.1.0/strimzi-crds-1.1.0.yaml
```

### 3단계: Strimzi Cluster Operator 설치
```bash
helm install strimzi-operator strimzi/strimzi-kafka-operator --namespace kafka
```

오퍼레이터 파드가 `1/1 Running` 상태가 되는지 확인합니다:
```bash
kubectl get pods -n kafka -w
```

### 4단계: Kafka 클러스터(KRaft 단일 노드) 배포
[`kafka-cluster.yaml`](./kafka-cluster.yaml) 파일을 생성하고 적용합니다.

```yaml
apiVersion: kafka.strimzi.io/v1
kind: KafkaNodePool
metadata:
  name: dual-role
  namespace: kafka
  labels:
    strimzi.io/cluster: my-cluster
spec:
  replicas: 1
  roles:
    - controller
    - broker
  storage:
    type: ephemeral
---
apiVersion: kafka.strimzi.io/v1
kind: Kafka
metadata:
  name: my-cluster
  namespace: kafka
spec:
  kafka:
    version: 4.3.0
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
      default.replication.factor: 1
      min.insync.replicas: 1
  entityOperator:
    topicOperator: {}
    userOperator: {}
```

```bash
kubectl apply -f kafka-cluster.yaml
```

---

## 3. 🔥 트러블슈팅 케이스: CRD 버전 불일치로 인한 CrashLoopBackOff

### 1) 발생 현상
Strimzi 오퍼레이터를 설치한 후 파드가 `Running`과 `Error`를 반복하다가 `CrashLoopBackOff`에 빠짐.
```text
NAME                                        READY   STATUS             RESTARTS   AGE
strimzi-cluster-operator-5b7cf875f4-cqrpc   0/1     CrashLoopBackOff   3          94s
```

### 2) 원인 진단 및 로그 분석
- **직전 종료된 컨테이너의 로그 확인:**
  ```bash
  kubectl logs -n kafka strimzi-cluster-operator-5b7cf875f4-cqrpc --previous
  ```
- **핵심 에러 로그:**
  ```text
  ERROR Informer: Caught exception in the KafkaMirrorMaker2 informer which is not started
  io.fabric8.kubernetes.client.KubernetesClientException: Failure executing: 
  GET at: https://10.96.0.1:443/apis/kafka.strimzi.io/v1/namespaces/kafka/kafkamirrormaker2s?resourceVersion=0. Message: Not Found.
  ```
- **원인 분석**:
  - 오퍼레이터(1.1.0)는 `kafka.strimzi.io/v1` API를 요청했으나, 쿠버네티스에는 과거 설치된 `v1beta2` 버전의 CRD만 존재하여 404(`Not Found`) 반환.

### 3) CRD 확인 및 충돌 해결 과정
1. **CRD 버전 확인:**
   ```bash
   kubectl get crd kafkamirrormaker2s.kafka.strimzi.io -o yaml | grep -A 5 "versions:"
   # 확인 결과: v1beta2만 존재 (v1 부재)
   ```
2. **`kubectl apply` 시 `status.storedVersions` 에러 발생:**
   ```text
   CustomResourceDefinition "kafkarebalances.kafka.strimzi.io" is invalid: status.storedVersions[0]: Invalid value: "v1beta2"
   ```
   - k8s는 데이터 손실 방지를 위해 기존 저장 버전(`v1beta2`)이 새 CRD 정의에서 누락되면 apply를 거부함.
3. **해결 조치 (기존 카프카 리소스가 없는 환경):**
   - 구버전 CRD 일괄 삭제 후 최신 v1 CRD 재등록:
   ```bash
   # 1. 구버전 CRD 삭제
   kubectl get crd -o name | grep strimzi.io | xargs kubectl delete

   # 2. 1.1.0 CRD 재적용
   kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/1.1.0/strimzi-crds-1.1.0.yaml

   # 3. 오퍼레이터 파드 재기동
   kubectl delete pod -n kafka -l name=strimzi-cluster-operator
   ```

---

## 4. 주요 학습 포인트

1. **Helm의 CRD 관리 한계:**
   - Helm은 리소스 충돌과 데이터 삭제를 방지하기 위해 `crds/` 하위의 CRD를 `helm upgrade` 시 자동으로 갱신하거나 삭제하지 않습니다.
   - 따라서 오퍼레이터 버전 업그레이드 시에는 반드시 **CRD 매니페스트를 별도로 `kubectl apply`** 해주어야 합니다.
2. **쿠버네티스 CRD 스토리지 버전(`storedVersions`) 규칙:**
   - CRD에서 이전 메이저/마이너 버전이 제거될 때는 기존에 저장된 데이터의 스토리지 마이그레이션이 필요합니다.
   - 신규/학습 환경에서는 기존 충돌 CRD를 깨끗이 삭제(`delete`) 후 재설치하는 것이 가장 빠르고 안전합니다.
