# airflow/dags/kafka_producer_pipeline.py
"""
[실전 파이프라인] Airflow에서 보안 인증(SASL/SCRAM)을 거쳐 Kafka 토픽으로 실시간 주문 데이터를 발행하는 DAG
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import json
import random
import time

default_args = {
    'owner': 'pihet',
    'start_date': datetime(2026, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='kafka_order_producer_pipeline', # 👈 대시보드에 뜰 파이프라인 이름
    default_args=default_args,
    description='카프카로 실시간 주문 이벤트 데이터를 전송하는 파이프라인',
    schedule=None,                          # 수동 실행
    catchup=False,
    tags=['kafka', 'commerce', 'realtime'],
) as dag:

    # 1. 시작 알림
    task_start = BashOperator(
        task_id='start_order_generation',
        bash_command='echo "=== Starting E-Commerce Order Event Stream ==="',
    )

    # 2. 카프카 토픽('my-topic')으로 보안 인증(SCRAM-SHA-512)을 거쳐 주문 메시지 전송
    # - 카프카 브로커 주소: my-cluster-kafka-bootstrap.kafka.svc:9092
    # - 보안 계정: my-app-user
    task_send_to_kafka = BashOperator(
        task_id='send_orders_to_kafka',
        bash_command="""
        # 1. 카프카 Secret에서 비밀번호 추출
        USER_PASS=$(kubectl get secret -n kafka my-app-user -o jsonpath='{.data.password}' | base64 --decode 2>/dev/null || echo "uk2eajtuFwLh3YcR12gK")
        
        # 2. 가상 주문 JSON 데이터 3건 생성
        ORDER_1='{"order_id": "ORD-1001", "user": "user_kim", "item": "MacBook Pro M3", "amount": 3200000, "timestamp": "'$(date -Iseconds)'"}'
        ORDER_2='{"order_id": "ORD-1002", "user": "user_lee", "item": "Sony WH-1000XM5", "amount": 450000, "timestamp": "'$(date -Iseconds)'"}'
        ORDER_3='{"order_id": "ORD-1003", "user": "user_park", "item": "Keychron K2", "amount": 120000, "timestamp": "'$(date -Iseconds)'"}'

        echo "Generated Orders:"
        echo "$ORDER_1"
        echo "$ORDER_2"
        echo "$ORDER_3"

        # 3. 임시 파드를 띄워 카프카 my-topic으로 메시지 보안 전송
        kubectl run kafka-airflow-producer -n kafka --image=quay.io/strimzi/kafka:1.2.0-kafka-4.3.1 --rm=true --restart=Never --attach=true -- /bin/bash -c "
        cat <<EOF > /tmp/client.properties
        security.protocol=SASL_PLAINTEXT
        sasl.mechanism=SCRAM-SHA-512
        sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username=\\\"my-app-user\\\" password=\\\"\$USER_PASS\\\";
        EOF

        echo '$ORDER_1' | bin/kafka-console-producer.sh --bootstrap-server my-cluster-kafka-bootstrap.kafka.svc:9092 --topic my-topic --producer.config /tmp/client.properties
        echo '$ORDER_2' | bin/kafka-console-producer.sh --bootstrap-server my-cluster-kafka-bootstrap.kafka.svc:9092 --topic my-topic --producer.config /tmp/client.properties
        echo '$ORDER_3' | bin/kafka-console-producer.sh --bootstrap-server my-cluster-kafka-bootstrap.kafka.svc:9092 --topic my-topic --producer.config /tmp/client.properties
        "
        """,
    )

    # 3. 완료 알림
    task_end = BashOperator(
        task_id='finish_pipeline',
        bash_command='echo "=== 3 Orders successfully published to Kafka topic [my-topic]! ==="',
    )

    task_start >> task_send_to_kafka >> task_end
