#!/usr/bin/env python3
"""
Production Database Seeding Script

Seeds the database with initial production data including:
- Fish species master data
- Default admin user
- System configuration

Multi-cloud compatible - works with PostgreSQL, SQL Server, and MySQL.
"""

import asyncio
import os
import sys
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Import models
from services.api.models.user import User
from services.api.models.prediction import FishSpecies, Model
from services.api.core.database import Base

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ProductionSeeder:
    """Production database seeder"""
    
    def __init__(self, database_url: str):
        """Initialize seeder with database URL"""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        print("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables created successfully")
    
    def seed_fish_species(self) -> None:
        """Seed fish species master data"""
        print("Seeding fish species data...")
        
        fish_species_data = [
            {
                "name": "Bangus",
                "scientific_name": "Chanos chanos",
                "description": "Milkfish, commonly farmed in Southeast Asia",
                "optimal_temperature_min": 25.0,
                "optimal_temperature_max": 32.0
            },
            {
                "name": "Tilapia",
                "scientific_name": "Oreochromis niloticus",
                "description": "Nile tilapia, popular freshwater aquaculture species",
                "optimal_temperature_min": 20.0,
                "optimal_temperature_max": 35.0
            },
            {
                "name": "Catfish",
                "scientific_name": "Clarias gariepinus",
                "description": "African catfish, hardy freshwater species",
                "optimal_temperature_min": 18.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Salmon",
                "scientific_name": "Salmo salar",
                "description": "Atlantic salmon, premium aquaculture species",
                "optimal_temperature_min": 6.0,
                "optimal_temperature_max": 16.0
            },
            {
                "name": "Grass_Carp",
                "scientific_name": "Ctenopharyngodon idella",
                "description": "Grass carp, herbivorous freshwater fish",
                "optimal_temperature_min": 15.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Big_Head_Carp",
                "scientific_name": "Hypophthalmichthys nobilis",
                "description": "Bighead carp, filter-feeding freshwater fish",
                "optimal_temperature_min": 12.0,
                "optimal_temperature_max": 28.0
            },
            {
                "name": "Silver_Carp",
                "scientific_name": "Hypophthalmichthys molitrix",
                "description": "Silver carp, planktivorous freshwater fish",
                "optimal_temperature_min": 10.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Indian_Carp",
                "scientific_name": "Labeo rohita",
                "description": "Rohu, major Indian carp species",
                "optimal_temperature_min": 18.0,
                "optimal_temperature_max": 32.0
            },
            {
                "name": "Pangasius",
                "scientific_name": "Pangasianodon hypophthalmus",
                "description": "Striped catfish, popular in Asian aquaculture",
                "optimal_temperature_min": 22.0,
                "optimal_temperature_max": 32.0
            },
            {
                "name": "Gourami",
                "scientific_name": "Osphronemus goramy",
                "description": "Giant gourami, freshwater aquaculture species",
                "optimal_temperature_min": 20.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Snakehead",
                "scientific_name": "Channa striata",
                "description": "Striped snakehead, predatory freshwater fish",
                "optimal_temperature_min": 18.0,
                "optimal_temperature_max": 32.0
            },
            {
                "name": "Climbing_Perch",
                "scientific_name": "Anabas testudineus",
                "description": "Climbing perch, air-breathing freshwater fish",
                "optimal_temperature_min": 20.0,
                "optimal_temperature_max": 35.0
            },
            {
                "name": "Janitor_Fish",
                "scientific_name": "Pterygoplichthys pardalis",
                "description": "Leopard pleco, bottom-dwelling catfish",
                "optimal_temperature_min": 22.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Knifefish",
                "scientific_name": "Notopterus notopterus",
                "description": "Bronze featherback, elongated freshwater fish",
                "optimal_temperature_min": 22.0,
                "optimal_temperature_max": 28.0
            },
            {
                "name": "Freshwater_Eel",
                "scientific_name": "Anguilla japonica",
                "description": "Japanese eel, catadromous species",
                "optimal_temperature_min": 15.0,
                "optimal_temperature_max": 25.0
            },
            {
                "name": "Glass_Perchlet",
                "scientific_name": "Parambassis ranga",
                "description": "Indian glassy fish, transparent freshwater species",
                "optimal_temperature_min": 20.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Goby",
                "scientific_name": "Glossogobius giuris",
                "description": "Tank goby, small bottom-dwelling fish",
                "optimal_temperature_min": 18.0,
                "optimal_temperature_max": 32.0
            },
            {
                "name": "Tenpounder",
                "scientific_name": "Elops machnata",
                "description": "Tenpounder, marine and brackish water fish",
                "optimal_temperature_min": 22.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Black_Spotted_Barb",
                "scientific_name": "Barbodes binotatus",
                "description": "Spotted barb, freshwater cyprinid",
                "optimal_temperature_min": 20.0,
                "optimal_temperature_max": 28.0
            },
            {
                "name": "Fourfinger_Threadfin",
                "scientific_name": "Eleutheronema tetradactylum",
                "description": "Fourfinger threadfin, marine and estuarine fish",
                "optimal_temperature_min": 24.0,
                "optimal_temperature_max": 32.0
            },
            {
                "name": "Green_Spotted_Puffer",
                "scientific_name": "Tetraodon nigroviridis",
                "description": "Green spotted puffer, brackish water species",
                "optimal_temperature_min": 22.0,
                "optimal_temperature_max": 28.0
            },
            {
                "name": "Indo_Pacific_Tarpon",
                "scientific_name": "Megalops cyprinoides",
                "description": "Indo-Pacific tarpon, large marine fish",
                "optimal_temperature_min": 24.0,
                "optimal_temperature_max": 32.0
            },
            {
                "name": "Jaguar_Gapote",
                "scientific_name": "Parachromis managuensis",
                "description": "Jaguar cichlid, Central American freshwater fish",
                "optimal_temperature_min": 22.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Long_Snouted_Pipefish",
                "scientific_name": "Syngnathus acus",
                "description": "Greater pipefish, marine syngnathid",
                "optimal_temperature_min": 18.0,
                "optimal_temperature_max": 25.0
            },
            {
                "name": "Mosquito_Fish",
                "scientific_name": "Gambusia affinis",
                "description": "Western mosquitofish, small freshwater fish",
                "optimal_temperature_min": 15.0,
                "optimal_temperature_max": 35.0
            },
            {
                "name": "Mudfish",
                "scientific_name": "Channa punctata",
                "description": "Spotted snakehead, air-breathing freshwater fish",
                "optimal_temperature_min": 18.0,
                "optimal_temperature_max": 32.0
            },
            {
                "name": "Mullet",
                "scientific_name": "Mugil cephalus",
                "description": "Flathead grey mullet, euryhaline species",
                "optimal_temperature_min": 15.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Perch",
                "scientific_name": "Perca fluviatilis",
                "description": "European perch, freshwater predatory fish",
                "optimal_temperature_min": 10.0,
                "optimal_temperature_max": 25.0
            },
            {
                "name": "Scat_Fish",
                "scientific_name": "Scatophagus argus",
                "description": "Spotted scat, brackish water species",
                "optimal_temperature_min": 22.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Silver_Barb",
                "scientific_name": "Barbonymus gonionotus",
                "description": "Java barb, freshwater cyprinid",
                "optimal_temperature_min": 20.0,
                "optimal_temperature_max": 30.0
            },
            {
                "name": "Silver_Perch",
                "scientific_name": "Bidyanus bidyanus",
                "description": "Murray cod, Australian freshwater fish",
                "optimal_temperature_min": 15.0,
                "optimal_temperature_max": 28.0
            }
        ]
        
        session = self.SessionLocal()
        try:
            for species_data in fish_species_data:
                # Check if species already exists
                existing = session.query(FishSpecies).filter(
                    FishSpecies.name == species_data["name"]
                ).first()
                
                if not existing:
                    species = FishSpecies(**species_data)
                    session.add(species)
            
            session.commit()
            print(f"✅ Seeded {len(fish_species_data)} fish species")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error seeding fish species: {e}")
            raise
        finally:
            session.close()
    
    def seed_admin_user(self) -> None:
        """Create default admin user"""
        print("Creating default admin user...")
        
        session = self.SessionLocal()
        try:
            # Check if admin user already exists
            existing_admin = session.query(User).filter(
                User.email == "admin@aquaculture.com"
            ).first()
            
            if not existing_admin:
                # Create admin user
                hashed_password = pwd_context.hash("admin123!@#")  # Change this in production!
                
                admin_user = User(
                    email="admin@aquaculture.com",
                    username="admin",
                    hashed_password=hashed_password,
                    full_name="System Administrator",
                    is_active=True,
                    is_superuser=True
                )
                
                session.add(admin_user)
                session.commit()
                print("✅ Created default admin user")
                print("   Email: admin@aquaculture.com")
                print("   Password: admin123!@# (CHANGE THIS IN PRODUCTION!)")
            else:
                print("ℹ️  Admin user already exists")
                
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating admin user: {e}")
            raise
        finally:
            session.close()
    
    def seed_default_model(self) -> None:
        """Create default ML model entry"""
        print("Creating default ML model entry...")
        
        session = self.SessionLocal()
        try:
            # Check if default model already exists
            existing_model = session.query(Model).filter(
                Model.name == "fish_classifier",
                Model.version == "v1.0.0"
            ).first()
            
            if not existing_model:
                # Get admin user ID
                admin_user = session.query(User).filter(
                    User.email == "admin@aquaculture.com"
                ).first()
                
                default_model = Model(
                    name="fish_classifier",
                    version="v1.0.0",
                    architecture="resnet50",
                    file_path="/app/models/v1.0.0/model.pth",
                    accuracy=0.945,
                    precision_score=0.942,
                    recall_score=0.938,
                    f1_score=0.940,
                    is_active=True,
                    model_metadata={
                        "training_date": "2024-01-15",
                        "training_samples": 50000,
                        "validation_accuracy": 0.945,
                        "species_count": 31,
                        "input_size": [224, 224],
                        "framework": "PyTorch",
                        "framework_version": "2.1.1"
                    },
                    created_by=admin_user.id if admin_user else None
                )
                
                session.add(default_model)
                session.commit()
                print("✅ Created default ML model entry")
            else:
                print("ℹ️  Default model already exists")
                
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating default model: {e}")
            raise
        finally:
            session.close()
    
    def run_all_seeds(self) -> None:
        """Run all seeding operations"""
        print("🌱 Starting production database seeding...")
        print(f"Database URL: {self.database_url}")
        
        try:
            self.create_tables()
            self.seed_fish_species()
            self.seed_admin_user()
            self.seed_default_model()
            
            print("\n🎉 Production database seeding completed successfully!")
            print("\n⚠️  IMPORTANT SECURITY NOTES:")
            print("1. Change the default admin password immediately")
            print("2. Create proper user accounts for production use")
            print("3. Ensure proper backup procedures are in place")
            print("4. Review and update fish species data as needed")
            
        except Exception as e:
            print(f"\n❌ Database seeding failed: {e}")
            raise


def main():
    """Main function"""
    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://aquaculture:CHANGE_PASSWORD@localhost:5432/aquaculture_db")
    )
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Initialize and run seeder
    seeder = ProductionSeeder(database_url)
    seeder.run_all_seeds()


if __name__ == "__main__":
    main()
