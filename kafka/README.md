# Apache Kafka on Kubernetes 운영 가이드

> Strimzi Operator 기반 3-노드 고가용성(HA) Kafka 브로커 클러스터 및 KRaft 컨트롤러 운영 가이드입니다.

---

## 1. 주요 파일별 역할 및 기능

- [`cluster/kafka-ha-cluster.yaml`](./cluster/kafka-ha-cluster.yaml): Strimzi 3-브로커 HA 클러스터 및 3-컨트롤러 노드 배포 매니페스트.
- [`cluster/kafka-single-node.yaml`](./cluster/kafka-single-node.yaml): 로컬 경량 테스트용 단일 브로커 Kafka 매니페스트.
- [`topics/kafka-topic.yaml`](./topics/kafka-topic.yaml): 파티션 3개, 복제본 3개로 구성된 `my-topic` 선언 매니페스트.
- [`users/app-user.yaml`](./users/app-user.yaml): SCRAM-SHA-512 인증 계정(`my-app-user`) 및 토픽 읽기/쓰기 ACL 권한 매니페스트.
- [`../kafka-ui/kafka-ui.yaml`](../kafka-ui/kafka-ui.yaml): Kafka 브로커 모니터링을 위한 Kafka-UI 웹 애플리케이션 매니페스트.

---

## 2. 인프라 배포 및 실행 명령어

```bash
# 1. Strimzi Operator 설치 및 Kafka HA 클러스터 배포
helm upgrade --install strimzi-kafka-operator strimzi/strimzi-kafka-operator -n kafka --create-namespace
kubectl apply -f kafka/cluster/kafka-ha-cluster.yaml

# 2. 토픽 및 보안 사용자 계정 배포
kubectl apply -f kafka/topics/kafka-topic.yaml
kubectl apply -f kafka/users/app-user.yaml

# 3. Kafka-UI 웹 대시보드 배포
kubectl apply -f kafka-ui/kafka-ui.yaml

# 4. 클러스터 내부에서 CLI 메시지 발행 및 소비 테스트
# 메시지 발행 (Producer)
kubectl exec -it -n kafka my-cluster-broker-0 -- bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic my-topic

# 메시지 소비 (Consumer)
kubectl exec -it -n kafka my-cluster-broker-0 -- bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic my-topic \
  --from-beginning
```

---

## 3. 핵심 에러 발생 시 해결법 (Troubleshooting)

- **에러 1: `Strimzi Operator CrashLoopBackOff (CRD 버전 충돌)`**
  - **원인**: 구버전 v1beta2 CRD 잔존으로 인해 최신 오퍼레이터 구동 실패.
  - **해결**: 최신 v1 CRD 재적용 후 오퍼레이터 재기동:
    ```bash
    kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/1.1.0/strimzi-crds-1.1.0.yaml
    kubectl delete pod -n kafka -l name=strimzi-cluster-operator
    ```
- **에러 2: `AuthenticationFailed / NoBrokersAvailable`**
  - **원인**: SCRAM-SHA-512 보안 계정 패스워드 불일치.
  - **해결**: k8s 시크릿에서 실제 자동 생성된 패스워드 추출 확인:
    ```bash
    kubectl get secret my-app-user -n kafka -o jsonpath='{.data.password}' | base64 -d
    ```
