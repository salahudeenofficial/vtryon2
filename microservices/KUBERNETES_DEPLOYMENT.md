# Kubernetes Deployment Manifests

## Overview

Each microservice is deployed as a Kubernetes Deployment with:
- Resource limits (CPU, GPU, Memory)
- ConfigMaps for configuration
- PersistentVolumeClaims for model storage
- Service for internal communication
- HPA for auto-scaling

---

## 1. Latent Encoder Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: latent-encoder
  namespace: vtryon
spec:
  replicas: 2
  selector:
    matchLabels:
      app: latent-encoder
  template:
    metadata:
      labels:
        app: latent-encoder
    spec:
      containers:
      - name: latent-encoder
        image: vtryon/latent-encoder:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
            nvidia.com/gpu: 1
          limits:
            cpu: "4"
            memory: "8Gi"
            nvidia.com/gpu: 1
        env:
        - name: MODEL_DIR
          value: "/models"
        - name: OUTPUT_DIR
          value: "/output"
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: latent-encoder-config
              key: log_level
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
        - name: output
          mountPath: /output
        - name: config
          mountPath: /config
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
      - name: output
        persistentVolumeClaim:
          claimName: output-pvc
      - name: config
        configMap:
          name: latent-encoder-config
---
apiVersion: v1
kind: Service
metadata:
  name: latent-encoder-service
  namespace: vtryon
spec:
  selector:
    app: latent-encoder
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: latent-encoder-hpa
  namespace: vtryon
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: latent-encoder
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 2. Text Encoder Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: text-encoder
  namespace: vtryon
spec:
  replicas: 2
  selector:
    matchLabels:
      app: text-encoder
  template:
    metadata:
      labels:
        app: text-encoder
    spec:
      containers:
      - name: text-encoder
        image: vtryon/text-encoder:latest
        resources:
          requests:
            cpu: "2"
            memory: "8Gi"
            nvidia.com/gpu: 1
          limits:
            cpu: "4"
            memory: "16Gi"
            nvidia.com/gpu: 1
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: text-encoder-service
  namespace: vtryon
spec:
  selector:
    app: text-encoder
  ports:
  - port: 80
    targetPort: 8080
```

---

## 3. Sampling Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sampling
  namespace: vtryon
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sampling
  template:
    metadata:
      labels:
        app: sampling
    spec:
      containers:
      - name: sampling
        image: vtryon/sampling:latest
        resources:
          requests:
            cpu: "4"
            memory: "16Gi"
            nvidia.com/gpu: 1
          limits:
            cpu: "8"
            memory: "32Gi"
            nvidia.com/gpu: 1
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: sampling-service
  namespace: vtryon
spec:
  selector:
    app: sampling
  ports:
  - port: 80
    targetPort: 8080
```

---

## 4. Decoding Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: decoding
  namespace: vtryon
spec:
  replicas: 2
  selector:
    matchLabels:
      app: decoding
  template:
    metadata:
      labels:
        app: decoding
    spec:
      containers:
      - name: decoding
        image: vtryon/decoding:latest
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
            nvidia.com/gpu: 1
          limits:
            cpu: "4"
            memory: "8Gi"
            nvidia.com/gpu: 1
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
        - name: output
          mountPath: /output
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
      - name: output
        persistentVolumeClaim:
          claimName: output-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: decoding-service
  namespace: vtryon
spec:
  selector:
    app: decoding
  ports:
  - port: 80
    targetPort: 8080
```

---

## 5. Shared Resources

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vtryon-config
  namespace: vtryon
data:
  vae_model_name: "qwen_image_vae.safetensors"
  clip_model_name: "qwen_2.5_vl_7b_fp8_scaled.safetensors"
  unet_model_name: "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
  lora_model_name: "Qwen-Image-Lightning-4steps-V2.0.safetensors"
  model_dir: "/models"
  output_dir: "/output"
```

### PersistentVolumeClaim for Models
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: models-pvc
  namespace: vtryon
spec:
  accessModes:
    - ReadOnlyMany
  resources:
    requests:
      storage: 500Gi
  storageClassName: fast-ssd
```

### PersistentVolumeClaim for Output
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: output-pvc
  namespace: vtryon
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Ti
  storageClassName: standard
```

---

## 6. Kafka Integration (Kubernetes)

### Kafka Deployment
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
  namespace: vtryon
spec:
  serviceName: kafka-headless
  replicas: 3
  template:
    spec:
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:latest
        ports:
        - containerPort: 9092
        env:
        - name: KAFKA_BROKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        volumeMounts:
        - name: kafka-data
          mountPath: /var/lib/kafka/data
  volumeClaimTemplates:
  - metadata:
      name: kafka-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

### Kafka Consumer Deployment Example
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: latent-encoder-consumer
  namespace: vtryon
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: consumer
        image: vtryon/latent-encoder:latest
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
        - name: KAFKA_GROUP_ID
          value: "latent-encoder-group"
        - name: MODE
          value: "kafka-consumer"
```

---

## 7. Triton Inference Server (Kubernetes)

### Triton Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: triton-inference-server
  namespace: vtryon
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: triton
        image: nvcr.io/nvidia/tritonserver:latest-py3
        args:
        - tritonserver
        - --model-repository=/models
        - --strict-model-config=false
        ports:
        - containerPort: 8000  # HTTP
        - containerPort: 8001  # gRPC
        - containerPort: 8002  # Metrics
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
        volumeMounts:
        - name: triton-models
          mountPath: /models
      volumes:
      - name: triton-models
        persistentVolumeClaim:
          claimName: triton-models-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: triton-service
  namespace: vtryon
spec:
  selector:
    app: triton
  ports:
  - name: http
    port: 8000
  - name: grpc
    port: 8001
  - name: metrics
    port: 8002
```

---

## Deployment Commands

```bash
# Create namespace
kubectl create namespace vtryon

# Apply all manifests
kubectl apply -f k8s/ -n vtryon

# Check pods
kubectl get pods -n vtryon

# Check services
kubectl get svc -n vtryon

# Check HPA
kubectl get hpa -n vtryon

# View logs
kubectl logs -f deployment/latent-encoder -n vtryon
```

