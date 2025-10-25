#!/usr/bin/env python3
"""
Database Seeding Script - Initialize with sample data

This script populates the database with initial data including:
- Fish species information
- ML model metadata  
- Default admin user
"""

import sys
import os
import uuid
from sqlalchemy.orm import Session

# Add the services directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.api.core.database import SessionLocal, engine
from services.api.models.prediction import Model, FishSpecies
from services.api.models.user import User
from services.api.core.security import get_password_hash


def seed_fish_species(db: Session):
    """Seed fish species data"""
    species_data = [
        {
            "name": "Atlantic Salmon",
            "scientific_name": "Salmo salar",
            "description": "Popular farmed fish with pink flesh and high omega-3 content",
            "optimal_temperature_min": 8.0,
            "optimal_temperature_max": 14.0
        },
        {
            "name": "Rainbow Trout", 
            "scientific_name": "Oncorhynchus mykiss",
            "description": "Freshwater fish with distinctive rainbow coloring along sides",
            "optimal_temperature_min": 10.0,
            "optimal_temperature_max": 16.0
        },
        {
            "name": "European Sea Bass",
            "scientific_name": "Dicentrarchus labrax", 
            "description": "Premium white fish popular in Mediterranean aquaculture",
            "optimal_temperature_min": 15.0,
            "optimal_temperature_max": 22.0
        },
        {
            "name": "Gilthead Seabream",
            "scientific_name": "Sparus aurata",
            "description": "Mediterranean fish with distinctive golden band on forehead",
            "optimal_temperature_min": 18.0,
            "optimal_temperature_max": 25.0
        },
        {
            "name": "Atlantic Cod",
            "scientific_name": "Gadus morhua", 
            "description": "White fish popular in commercial fishing, mild flavor",
            "optimal_temperature_min": 5.0,
            "optimal_temperature_max": 12.0
        },
        {
            "name": "Tilapia",
            "scientific_name": "Oreochromis niloticus",
            "description": "Widely farmed freshwater fish, excellent for aquaculture",
            "optimal_temperature_min": 22.0,
            "optimal_temperature_max": 30.0
        },
        {
            "name": "Carp",
            "scientific_name": "Cyprinus carpio",
            "description": "Hardy freshwater fish, important in Asian aquaculture",
            "optimal_temperature_min": 12.0,
            "optimal_temperature_max": 25.0
        }
    ]
    
    for species_info in species_data:
        existing = db.query(FishSpecies).filter(FishSpecies.name == species_info["name"]).first()
        if not existing:
            species = FishSpecies(**species_info)
            db.add(species)
    
    db.commit()
    print("✅ Fish species seeded")


def seed_models(db: Session):
    """Seed ML models data"""
    model = Model(
        id=uuid.uuid4(),
        name="AquaNet-CNN",
        version="2.1.0", 
        architecture="ResNet50-based CNN",
        file_path="/app/models/aquanet_v2.1.pth",
        accuracy=0.9420,
        precision_score=0.9380,
        recall_score=0.9450,
        f1_score=0.9415,
        is_active=True,
        metadata={
            "training_dataset": "AquaCulture-15K Dataset",
            "epochs": 150,
            "batch_size": 32,
            "optimizer": "AdamW",
            "learning_rate": 0.001,
            "data_augmentation": True,
            "input_size": "224x224x3",
            "classes": 7,
            "training_time_hours": 24.5
        }
    )
    
    existing = db.query(Model).filter(Model.name == "AquaNet-CNN", Model.version == "2.1.0").first()
    if not existing:
        db.add(model)
        db.commit()
        print("✅ ML model seeded")


def seed_admin_user(db: Session):
    """Create admin user"""
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@aquaculture.com",
        username="admin",
        full_name="System Administrator", 
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_superuser=True
    )
    
    existing = db.query(User).filter(User.username == "admin").first()
    if not existing:
        db.add(admin_user)
        db.commit()
        print("✅ Admin user created (admin/admin123)")


def seed_demo_user(db: Session):
    """Create demo user for testing"""
    demo_user = User(
        id=uuid.uuid4(),
        email="demo@aquaculture.com",
        username="demo",
        full_name="Demo User", 
        hashed_password=get_password_hash("demo123"),
        is_active=True,
        is_superuser=False
    )
    
    existing = db.query(User).filter(User.username == "demo").first()
    if not existing:
        db.add(demo_user)
        db.commit()
        print("✅ Demo user created (demo/demo123)")


def main():
    """Run database seeding"""
    print("🌱 Seeding Aquaculture ML Platform database...")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Create all tables first
        from services.api.models import user, prediction
        from services.api.core.database import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
        
        # Seed data
        seed_fish_species(db)
        seed_models(db)
        seed_admin_user(db)
        seed_demo_user(db)
        
        print("=" * 50)
        print("🎉 Database seeding completed successfully!")
        print("\n📋 Created accounts:")
        print("   • Admin: admin / admin123")
        print("   • Demo:  demo / demo123")
        print("\n🐟 Seeded 7 fish species")
        print("🤖 Seeded 1 ML model (AquaNet-CNN v2.1.0)")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()