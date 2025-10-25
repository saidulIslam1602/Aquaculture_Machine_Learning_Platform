# 🎯 **SRE Interview Mastery Guide**

## 📋 **Quick Reference for Interview Day**

### **Project Overview (30-second pitch)**
"I built a production-grade aquaculture ML platform with microservices architecture. It uses Docker for containerization, Kubernetes for orchestration, PostgreSQL for data persistence, Redis for caching, and Kafka for real-time streaming. The system includes comprehensive monitoring with Prometheus and Grafana, JWT authentication, and is designed to handle 500-2000 requests per second with 99.9% availability."

---

## 🏗️ **Architecture Deep Dive**

### **System Components**

```
┌─────────────────────────────────────────────────────────────┐
│                   NGINX Load Balancer                       │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐   ┌───▼────┐   ┌──▼─────┐
   │  API   │   │   ML   │   │ Worker │
   │Service │   │Service │   │Service │
   │:8000   │   │:8001   │   │(Celery)│
   └────┬───┘   └───┬────┘   └──┬─────┘
        │           │            │
        └───────────┼────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   ┌────▼────┐ ┌───▼────┐ ┌───▼────┐
   │PostgreSQL│ │ Redis  │ │ Kafka  │
   │:5432     │ │:6379   │ │:9092   │
   └─────────┘ └────────┘ └────────┘
```

### **Data Flow Patterns**

1. **Synchronous Request Flow**:
   ```
   User → NGINX → API Service → Database → Response
   ```

2. **Asynchronous Processing Flow**:
   ```
   User → API → Kafka → Worker → ML Service → Database
   ```

3. **Monitoring Flow**:
   ```
   All Services → Prometheus → Grafana → Alerts → PagerDuty/Slack
   ```

---

## 🐳 **Docker & Containerization**

### **Key Interview Points**

#### **Multi-stage Dockerfile Benefits**
```dockerfile
# Stage 1: Builder (includes build tools)
FROM python:3.10-slim as builder
RUN apt-get update && apt-get install -y gcc g++ libpq-dev
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime (minimal dependencies)
FROM python:3.10-slim
RUN apt-get update && apt-get install -y libpq5 curl
COPY --from=builder /root/.local /root/.local
# ... rest of runtime setup
```

**Benefits**:
- **Smaller Images**: 200MB vs 800MB (build tools excluded)
- **Security**: Fewer attack vectors in production
- **Performance**: Faster deployment and startup

#### **Health Check Strategy**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**Why This Approach**:
- **Container Orchestration**: Kubernetes uses health checks for traffic routing
- **Load Balancer Integration**: NGINX removes unhealthy containers
- **Monitoring**: Prometheus scrapes health status

#### **Security Best Practices**
```dockerfile
# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Read-only root filesystem (in Kubernetes)
securityContext:
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
```

### **Docker Compose Orchestration**

#### **Service Dependencies**
```yaml
api:
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
```

**Why Dependency Management**:
- **Startup Order**: Database must be ready before API
- **Health Checks**: Ensures services are actually ready, not just started
- **Failure Handling**: Automatic restart if dependencies fail

---

## ☸️ **Kubernetes Orchestration**

### **Deployment Strategy**

#### **Rolling Updates (Zero Downtime)**
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1          # Can have 1 extra pod during update
    maxUnavailable: 0    # Never have fewer than desired replicas
```

**Interview Question**: "How do you achieve zero-downtime deployments?"
**Answer**: 
1. Rolling updates with `maxUnavailable: 0`
2. Readiness probes ensure new pods are ready before receiving traffic
3. Graceful shutdown handling in application
4. Database migrations run as init containers

#### **Health Check Implementation**
```yaml
livenessProbe:
  httpGet:
    path: /live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3
```

**Difference Between Probes**:
- **Liveness**: "Is the application alive?" (restart if fails)
- **Readiness**: "Is the application ready for traffic?" (remove from load balancer if fails)
- **Startup**: "Is the application starting up?" (gives extra time for slow-starting apps)

#### **Resource Management**
```yaml
resources:
  requests:
    memory: "256Mi"    # Guaranteed resources
    cpu: "250m"        # 0.25 CPU cores
  limits:
    memory: "512Mi"    # Maximum allowed
    cpu: "500m"        # Maximum CPU usage
```

**Why Resource Limits**:
- **Quality of Service**: Guaranteed vs Burstable vs BestEffort
- **Node Scheduling**: Kubernetes knows resource requirements
- **Protection**: Prevents one pod from consuming all resources

### **Horizontal Pod Autoscaler (HPA)**
```yaml
spec:
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

**Scaling Decisions**:
- **CPU-based**: Scale when average CPU > 70%
- **Memory-based**: Scale when memory usage high
- **Custom Metrics**: Scale based on queue length, response time
- **Predictive Scaling**: Based on historical patterns

---

## 📊 **Monitoring & Observability**

### **Four Pillars of Observability**

#### **1. Metrics (Prometheus)**
```yaml
# Key SRE Metrics
- API Latency (p50, p95, p99)
- Error Rate (4xx, 5xx responses)
- Throughput (requests per second)
- Saturation (CPU, memory, disk usage)
```

#### **2. Logs (ELK Stack)**
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "ERROR",
  "service": "api",
  "trace_id": "abc123",
  "user_id": "user456",
  "endpoint": "/api/v1/predict",
  "error": "Database connection timeout",
  "duration_ms": 5000
}
```

#### **3. Traces (Jaeger)**
```
Request Trace:
├── API Gateway (2ms)
├── Authentication (5ms)
├── API Service (45ms)
│   ├── Database Query (30ms)
│   └── Cache Lookup (2ms)
└── Response Serialization (3ms)
Total: 55ms
```

#### **4. Alerts (Alertmanager)**
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "API error rate is {{ $value | humanizePercentage }}"
```

### **SLI/SLO Framework**

#### **Service Level Indicators (SLIs)**
- **Availability**: `sum(rate(http_requests_total{status!~"5.."}[5m])) / sum(rate(http_requests_total[5m]))`
- **Latency**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Error Rate**: `rate(http_requests_total{status=~"5.."}[5m])`

#### **Service Level Objectives (SLOs)**
- **Availability**: 99.9% (8.76 hours downtime/year)
- **Latency**: 95% of requests < 100ms
- **Error Rate**: < 0.1% of requests

#### **Error Budget**
```
Error Budget = (1 - SLO) × Total Requests
Example: (1 - 0.999) × 1,000,000 = 1,000 errors allowed per month
```

---

## 🚨 **Incident Response & Troubleshooting**

### **Common SRE Scenarios**

#### **Scenario 1: API Latency Spike**

**Symptoms**: p95 latency > 2 seconds
**Investigation Steps**:
1. **Check Grafana Dashboard**: Identify when spike started
2. **Database Performance**: Check slow query log, connection pool
3. **Resource Utilization**: CPU, memory usage on pods
4. **External Dependencies**: Redis, Kafka connectivity
5. **Recent Deployments**: Correlate with deployment timeline

**Resolution Actions**:
```bash
# Scale up immediately
kubectl scale deployment api-service --replicas=10

# Check database connections
kubectl exec -it postgres-pod -- psql -c "SELECT count(*) FROM pg_stat_activity;"

# Review slow queries
kubectl logs deployment/api-service | grep "slow query"

# Check resource usage
kubectl top pods -n aquaculture-prod
```

#### **Scenario 2: Service Outage**

**Symptoms**: API returning 503 errors
**Investigation Steps**:
1. **Service Status**: `kubectl get pods -n aquaculture-prod`
2. **Pod Logs**: `kubectl logs deployment/api-service --tail=100`
3. **Events**: `kubectl get events -n aquaculture-prod --sort-by='.lastTimestamp'`
4. **Dependencies**: Check database, Redis connectivity

**Resolution Actions**:
```bash
# Check pod status
kubectl describe pod api-service-xxx

# Restart deployment
kubectl rollout restart deployment/api-service

# Check resource limits
kubectl describe deployment api-service

# Emergency rollback
kubectl rollout undo deployment/api-service
```

#### **Scenario 3: Memory Leak**

**Symptoms**: Pods getting OOMKilled
**Investigation Steps**:
1. **Memory Usage Trends**: Grafana memory dashboard
2. **Application Metrics**: Check for memory leaks in code
3. **Garbage Collection**: Python/Java GC metrics
4. **Resource Limits**: Compare usage vs limits

**Resolution Actions**:
```bash
# Increase memory limits temporarily
kubectl patch deployment api-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"memory":"1Gi"}}}]}}}}'

# Enable memory profiling
kubectl set env deployment/api-service PYTHONMALLOC=debug

# Monitor heap usage
kubectl exec -it api-pod -- python -c "import psutil; print(psutil.virtual_memory())"
```

### **Runbook Template**

```markdown
# API Service Down Runbook

## Symptoms
- Health check failing
- 503 errors from load balancer
- Prometheus alert: APIDown

## Investigation
1. Check pod status: `kubectl get pods -l app=api-service`
2. Check logs: `kubectl logs -l app=api-service --tail=50`
3. Check events: `kubectl get events --sort-by='.lastTimestamp'`

## Resolution
1. Restart pods: `kubectl rollout restart deployment/api-service`
2. If persistent, rollback: `kubectl rollout undo deployment/api-service`
3. Scale up: `kubectl scale deployment api-service --replicas=5`

## Escalation
- If not resolved in 15 minutes, page on-call engineer
- If database issue, contact DBA team
```

---

## 🔒 **Security & Compliance**

### **Security Layers**

#### **Network Security**
```yaml
# Network Policy Example
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: api-service
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8000
```

**Benefits**:
- **Micro-segmentation**: Limit communication between services
- **Zero Trust**: Default deny, explicit allow
- **Compliance**: Meet security requirements

#### **Container Security**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

#### **Secret Management**
```yaml
# Kubernetes Secret
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
type: Opaque
data:
  database-password: <base64-encoded>
  jwt-secret: <base64-encoded>
```

**Best Practices**:
- **Encryption at Rest**: Kubernetes etcd encryption
- **Rotation**: Regular secret rotation
- **Least Privilege**: Minimal RBAC permissions
- **Audit Logging**: Track secret access

---

## 🚀 **Performance & Scalability**

### **Scaling Strategies**

#### **Horizontal Scaling**
```yaml
# HPA Configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

#### **Vertical Scaling**
```yaml
# VPA Configuration
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  updatePolicy:
    updateMode: "Auto"
```

### **Performance Optimization**

#### **Database Optimization**
```python
# Connection Pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Number of persistent connections
    max_overflow=30,        # Additional connections when needed
    pool_pre_ping=True,     # Verify connections before use
    pool_recycle=3600,      # Recycle connections every hour
)
```

#### **Caching Strategy**
```python
# Redis Caching
@cache.memoize(timeout=300)  # 5 minute cache
async def get_user_profile(user_id: int):
    # Expensive database query
    return await db.query(User).filter(User.id == user_id).first()
```

#### **Async Processing**
```python
# FastAPI Async Endpoints
@app.post("/predict/async")
async def predict_async(image: UploadFile):
    # Queue for background processing
    task = predict_image.delay(image.file.read())
    return {"task_id": task.id}
```

---

## 📈 **Capacity Planning**

### **Resource Forecasting**

#### **CPU Usage Prediction**
```promql
# Predict CPU usage growth
predict_linear(
  avg(rate(container_cpu_usage_seconds_total[5m])) by (pod)[1h:5m], 
  3600 * 24 * 7  # 7 days ahead
)
```

#### **Memory Growth Analysis**
```promql
# Memory usage trend
increase(
  container_memory_usage_bytes{pod=~"api-.*"}[24h]
)
```

#### **Traffic Forecasting**
```promql
# Request rate growth
predict_linear(
  rate(http_requests_total[5m])[1h:5m], 
  3600 * 24 * 30  # 30 days ahead
)
```

### **Capacity Planning Metrics**

| Metric | Current | Target | Action Threshold |
|--------|---------|--------|------------------|
| CPU Utilization | 45% | 70% | 60% |
| Memory Usage | 60% | 80% | 75% |
| Disk Usage | 30% | 70% | 60% |
| Request Rate | 500 RPS | 2000 RPS | 1500 RPS |

---

## 🎯 **Interview Questions & Answers**

### **System Design Questions**

**Q: "How would you scale this system to handle 10x traffic?"**

**A**: "I'd implement a multi-layered scaling approach:

1. **Horizontal Scaling**: Increase HPA max replicas from 20 to 100
2. **Database Scaling**: 
   - Read replicas for query distribution
   - Connection pooling optimization
   - Query optimization and indexing
3. **Caching**: 
   - Redis cluster for high availability
   - CDN for static content
   - Application-level caching
4. **Load Balancing**: 
   - Multiple NGINX instances
   - Geographic load balancing
5. **Async Processing**: 
   - More Kafka partitions
   - Additional Celery workers
6. **Monitoring**: 
   - Enhanced alerting thresholds
   - Capacity planning dashboards"

**Q: "How do you ensure 99.99% availability?"**

**A**: "To achieve 99.99% availability (52 minutes downtime/year):

1. **Redundancy**: 
   - Multi-AZ deployment
   - Database replication
   - Load balancer redundancy
2. **Health Checks**: 
   - Comprehensive liveness/readiness probes
   - Circuit breakers for external dependencies
3. **Deployment Strategy**: 
   - Blue-green deployments
   - Canary releases for risk mitigation
4. **Monitoring**: 
   - Real-time alerting with <5 minute MTTD
   - Automated remediation for common issues
5. **Disaster Recovery**: 
   - Regular backup testing
   - Documented runbooks
   - Chaos engineering practices"

### **Troubleshooting Questions**

**Q: "API response time suddenly increased from 50ms to 2 seconds. How do you investigate?"**

**A**: "I'd follow this systematic approach:

1. **Immediate Triage** (0-5 minutes):
   - Check Grafana dashboards for timeline correlation
   - Verify if it's affecting all endpoints or specific ones
   - Check if error rates increased simultaneously

2. **Infrastructure Investigation** (5-15 minutes):
   - CPU/Memory usage on API pods: `kubectl top pods`
   - Database connection pool status
   - Network latency between services
   - Recent deployments or configuration changes

3. **Application-Level Analysis** (15-30 minutes):
   - Slow query logs in PostgreSQL
   - Redis cache hit rates
   - Distributed tracing with Jaeger
   - Application logs for errors or warnings

4. **Resolution Actions**:
   - Scale up pods if resource constrained
   - Restart services if memory leak suspected
   - Rollback if correlated with recent deployment
   - Optimize queries if database bottleneck identified"

**Q: "How do you handle a complete database outage?"**

**A**: "Database outage response plan:

1. **Immediate Response** (0-2 minutes):
   - Activate incident response team
   - Switch API to maintenance mode
   - Notify stakeholders via status page

2. **Assessment** (2-10 minutes):
   - Determine if primary or replica failure
   - Check backup systems availability
   - Estimate recovery time

3. **Recovery Actions**:
   - **If replica available**: Promote replica to primary
   - **If backup needed**: Restore from latest backup
   - **If corruption**: Point-in-time recovery

4. **Service Restoration**:
   - Verify data integrity
   - Gradually restore traffic
   - Monitor for cascading failures

5. **Post-Incident**:
   - Root cause analysis
   - Update runbooks
   - Implement preventive measures"

### **Architecture Questions**

**Q: "Why did you choose microservices over monolith?"**

**A**: "I chose microservices for several reasons:

1. **Scalability**: Different services have different scaling needs
   - API service: High request volume
   - ML service: CPU/GPU intensive
   - Worker service: Queue-based scaling

2. **Technology Diversity**: 
   - API: FastAPI for web performance
   - ML: PyTorch for model inference
   - Worker: Celery for background tasks

3. **Team Independence**: 
   - Separate deployment cycles
   - Independent development teams
   - Isolated failure domains

4. **Operational Benefits**:
   - Service-specific monitoring
   - Granular resource allocation
   - Independent security policies

However, I acknowledge the tradeoffs:
- Increased operational complexity
- Network latency between services
- Distributed system challenges (consistency, debugging)"

**Q: "How do you handle service-to-service communication?"**

**A**: "I implement multiple communication patterns:

1. **Synchronous Communication**:
   - HTTP/REST for real-time requests
   - Service discovery via Kubernetes DNS
   - Circuit breakers for fault tolerance
   - Retry policies with exponential backoff

2. **Asynchronous Communication**:
   - Kafka for event streaming
   - Message queues for background tasks
   - Event-driven architecture for loose coupling

3. **Security**:
   - mTLS for service-to-service encryption
   - JWT tokens for authentication
   - Network policies for traffic control

4. **Observability**:
   - Distributed tracing with correlation IDs
   - Service mesh (Istio) for advanced traffic management
   - Comprehensive logging at service boundaries"

---

## 🎯 **Demo Script for Interview**

### **5-Minute Live Demo**

#### **1. Architecture Overview (1 minute)**
```bash
# Show project structure
tree -L 3 aquaculture-ml-platform/

# Explain key directories
echo "infrastructure/ - Docker, Kubernetes, Terraform"
echo "monitoring/ - Prometheus, Grafana, Alertmanager"
echo "services/ - API, ML, Worker microservices"
```

#### **2. Start the System (1 minute)**
```bash
# Start all services
./scripts/start.sh

# Show running containers
docker-compose ps

# Check health
curl http://localhost:8000/health
```

#### **3. Show Monitoring (1 minute)**
```bash
# Open Grafana dashboard
open http://localhost:3000

# Show Prometheus targets
open http://localhost:9090/targets

# Demonstrate metrics
curl http://localhost:8000/metrics | head -20
```

#### **4. Demonstrate Scaling (1 minute)**
```bash
# Show current pods
kubectl get pods -n aquaculture-prod

# Scale up
kubectl scale deployment api-service --replicas=5

# Show HPA in action
kubectl get hpa -n aquaculture-prod
```

#### **5. Troubleshooting Demo (1 minute)**
```bash
# Simulate failure
kubectl delete pod api-service-xxx

# Show recovery
kubectl get pods -w

# Check logs
kubectl logs deployment/api-service --tail=10
```

---

## 📚 **Final Preparation Checklist**

### **Technical Knowledge**
- [ ] Can explain every component in the architecture
- [ ] Understand Docker multi-stage builds and security
- [ ] Know Kubernetes deployment strategies
- [ ] Familiar with Prometheus queries and alerting
- [ ] Can troubleshoot common issues

### **Operational Knowledge**
- [ ] Understand SLI/SLO/Error Budget concepts
- [ ] Know incident response procedures
- [ ] Familiar with capacity planning
- [ ] Understand security best practices
- [ ] Can explain monitoring strategy

### **Hands-on Skills**
- [ ] Can start the entire system with one command
- [ ] Can demonstrate scaling and monitoring
- [ ] Can simulate and recover from failures
- [ ] Can show CI/CD pipeline in action
- [ ] Can navigate Kubernetes resources

### **Communication Skills**
- [ ] Can explain complex concepts simply
- [ ] Can draw architecture diagrams
- [ ] Can tell stories about design decisions
- [ ] Can discuss tradeoffs and alternatives
- [ ] Can handle follow-up questions confidently

---

## 🏆 **Success Indicators**

### **During the Interview**
- Interviewer asks detailed follow-up questions
- Discussion moves from "what" to "why" and "how"
- Interviewer seems impressed by depth of knowledge
- You can answer questions without hesitation
- You demonstrate both breadth and depth

### **Red Flags to Avoid**
- ❌ "I used AI to build this"
- ❌ "I don't remember how this works"
- ❌ "It's just a demo project"
- ❌ "I followed a tutorial"
- ❌ "I'm not sure about the details"

### **Green Flags to Aim For**
- ✅ "I chose this approach because..."
- ✅ "The tradeoff here is..."
- ✅ "In production, I would also consider..."
- ✅ "Let me show you how this works..."
- ✅ "I've handled this scenario before..."

Remember: You're not just showing a project, you're demonstrating your ability to design, build, and operate production systems. Show confidence, depth of understanding, and practical experience!
