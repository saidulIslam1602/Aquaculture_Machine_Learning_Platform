# 🚀 Getting Started with Aquaculture ML Platform

<!--
============================================================================
GETTING STARTED GUIDE - DEVELOPER ONBOARDING
============================================================================

This guide provides a streamlined onboarding experience for developers,
data scientists, and DevOps engineers working with the Aquaculture ML Platform.

GUIDE OBJECTIVES:
- Zero-to-running platform in under 5 minutes
- Comprehensive feature overview and capabilities
- Development environment setup instructions
- API usage examples and best practices
- Troubleshooting common setup issues

LEARNING PATH:
1. Quick deployment for immediate hands-on experience
2. Platform exploration and feature discovery
3. Development workflow and contribution guidelines
4. Advanced configuration and customization

TARGET OUTCOMES:
- Fully functional local development environment
- Understanding of platform architecture and capabilities
- Ability to make first API calls and predictions
- Confidence to begin development contributions
============================================================================
-->

> **🏆 Enterprise-Grade ML Platform for Aquaculture Intelligence**

This comprehensive guide will help you deploy and explore the complete Aquaculture ML Platform in under 5 minutes, featuring **production-ready AI capabilities**, **modern web interface**, and **enterprise monitoring stack**.

## 🎯 What You'll Get

After following this guide:
- 🤖 **AI Fish Classification** - Upload images, get species identification
- 🎛️ **Web Dashboard** - Modern React interface
- 📊 **Analytics** - Track predictions and model performance
- 🔒 **User Management** - Secure authentication system
- 📈 **Monitoring** - Prometheus & Grafana dashboards

## 📋 Prerequisites

Ensure you have these installed:

```bash
# Check Docker
docker --version
# Should show: Docker version 20.10.x or higher

# Check Docker Compose
docker-compose --version
# Should show: Docker Compose version 2.x or higher
```

**System Requirements:**
- 8GB+ RAM recommended
- 10GB+ disk space
- Internet connection (for Docker images)

If not installed:
- **Docker**: https://docs.docker.com/get-docker/
- **Docker Compose**: https://docs.docker.com/compose/install/

## 🚀 One-Command Deployment

```bash
# Navigate to project directory
cd /home/saidul/Desktop/Aquaculture_Machine_Learning_Platform

# Run the quick start script (this does everything automatically)
./scripts/quickstart.sh
```

**That's it!** The script will:
- ✅ Check prerequisites
- ✅ Create environment file
- ✅ Start all Docker services
- ✅ Wait for services to be healthy
- ✅ Seed database with demo data
- ✅ Display access information

## 🌐 Access Your Platform

After successful deployment:

### **Main Applications**
- 🎛️ **Frontend Dashboard**: http://localhost:3000
- 🔧 **API Backend**: http://localhost:8000
- 📚 **Interactive API Docs**: http://localhost:8000/docs

### **Monitoring & Analytics**
- 📊 **Prometheus Metrics**: http://localhost:9090
- 📈 **Grafana Dashboards**: http://localhost:3001 (admin/admin)

### **Demo Accounts** (Pre-created)
- **Admin**: `admin` / `admin123`
- **Demo User**: `demo` / `demo123`

## 🧪 Test the System

### **1. Automated API Testing**
```bash
# Run comprehensive API tests
python3 scripts/test_api.py

# Expected output:
# ✅ Health Check
# ✅ User Login
# ✅ Get Model Info
# ✅ Fish Species Classification
# 🎉 All tests passed!
```

### **2. Manual Frontend Testing**
1. Go to http://localhost:3000
2. Login with `demo` / `demo123`
3. Upload a fish image (any image works for demo)
4. View the AI prediction results
5. Check your prediction history

### **3. API Documentation Testing**
1. Visit http://localhost:8000/docs
2. Click "Authorize" and login
3. Try the `/predictions/classify` endpoint
4. Upload an image and see real-time classification
  ## 🐟 Available Fish Species

The ML model can classify these species:
- 🐟 **Salmon** - High-value farmed fish
- 🐠 **Tuna** - Commercial ocean fish  
- 🎣 **Bass** - Popular sport/farm fish
- 🦈 **Shark** - Marine predator species
- 🐡 **Cod** - White fish variety
- 🦞 **Trout** - Freshwater species
- 🐟 **Other** - Unrecognized species

## 🔧 Advanced Configuration

### **Environment Variables** (Optional)
```bash
# Copy and edit configuration
cp .env.example .env
nano .env

# Key settings:
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379
ML_MODEL_PATH=/models/fish_classifier.h5
JWT_SECRET_KEY=your-secret-key
```

### **Manual Service Management**
```bash
# Start individual services
docker-compose up -d postgres redis
docker-compose up -d api ml-service
docker-compose up -d prometheus grafana

# View logs
docker-compose logs -f api
docker-compose logs --tail=100 ml-service

# Scale services
docker-compose up -d --scale api=3
```

## 🩺 Health Monitoring

### **Service Health Checks**
```bash
# Check all services
curl http://localhost:8000/health

# Check ML service specifically  
curl http://localhost:8000/api/v1/models/health

# Check database connectivity
curl http://localhost:8000/api/v1/health/database
```

### **System Metrics**
- **Response Times**: API latency tracking
- **Classification Accuracy**: ML model performance
- **Resource Usage**: CPU, memory, disk monitoring
- **Error Rates**: Failed requests and exceptions

## 📊 Dashboard Features

### **User Dashboard** (http://localhost:3000)
- 🎯 **Real-time fish classification**
- 📈 **Prediction history and analytics**
- 🎛️ **Farm management interface** 
- 📋 **Species identification results**
- 🔐 **Secure user authentication**

### **Admin Tools** (Login as admin)
- 👥 **User management**
- 🏭 **Farm monitoring**
- 📊 **System analytics**
- ⚙️ **Configuration management**

## 🚨 Troubleshooting

### **Quick Fixes**
```bash
# Restart everything
docker-compose restart

# Reset database (⚠️ Deletes all data)
docker-compose down -v
./scripts/quickstart.sh

# Check service status
docker-compose ps
docker-compose logs api
```

### **Common Issues**
1. **Port conflicts**: Change ports in `docker-compose.yml`
2. **Out of memory**: Increase Docker memory limits
3. **API not responding**: Check `docker-compose logs api`
4. **ML predictions failing**: Verify model file exists

## 🎯 Next Steps

1. **📖 Read the docs**: Check `/docs/` for detailed guides
2. **🔬 Run tests**: `python3 scripts/test_api.py`
3. **📊 Explore monitoring**: Visit Grafana dashboards
4. **🚀 Deploy to production**: See infrastructure configs
5. **🔧 Customize ML model**: Add your trained models
```

### Login and Get Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo12345"
```

Save the `access_token` from the response!

## Common Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api

# Restart services
docker-compose restart

# Stop services
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Remove everything including data
docker-compose down -v
```

## Troubleshooting

### Services not starting?

```bash
# Check logs
docker-compose logs

# Rebuild and restart
docker-compose up -d --build
```

### Port already in use?

```bash
# Find what's using the port
sudo lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

### Database connection issues?

```bash
# Check PostgreSQL is ready
docker-compose exec postgres pg_isready -U aquaculture

# Connect to database
docker-compose exec postgres psql -U aquaculture -d aquaculture_db
```

## Next Steps

- Read [SETUP.md](SETUP.md) for detailed configuration
- Read [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) for what's included
- Explore API at http://localhost:8000/docs
- Set up Grafana dashboards at http://localhost:3000

## Need Help?

1. Check the logs: `docker-compose logs -f`
2. Verify health: `curl http://localhost:8000/health/detailed`
3. Review documentation in `docs/` folder

---

**You're all set! 🎉**
