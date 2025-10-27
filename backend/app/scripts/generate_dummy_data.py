"""
Script to generate dummy data for testing the Composite Management System
"""
import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import SessionLocal
from app.models.material import Material
from app.models.composite import Composite, CompositeComponent, CompositeOrigin, CompositeStatus, ComponentType
from app.models.chromatographic_analysis import ChromatographicAnalysis
from app.models.user import User, UserRole
from passlib.context import CryptContext
import pandas as pd

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fragrance components with CAS numbers
FRAGRANCE_COMPONENTS = [
    {"name": "Limonene", "cas": "5989-27-5", "typical_pct": (15, 45)},
    {"name": "Linalool", "cas": "78-70-6", "typical_pct": (5, 25)},
    {"name": "Citral", "cas": "5392-40-5", "typical_pct": (1, 8)},
    {"name": "Geraniol", "cas": "106-24-1", "typical_pct": (2, 15)},
    {"name": "Citronellol", "cas": "106-22-9", "typical_pct": (3, 20)},
    {"name": "Alpha-Pinene", "cas": "80-56-8", "typical_pct": (10, 30)},
    {"name": "Beta-Pinene", "cas": "127-91-3", "typical_pct": (5, 15)},
    {"name": "Eugenol", "cas": "97-53-0", "typical_pct": (1, 10)},
    {"name": "Coumarin", "cas": "91-64-5", "typical_pct": (0.5, 5)},
    {"name": "Benzyl Alcohol", "cas": "100-51-6", "typical_pct": (2, 12)},
    {"name": "Benzyl Benzoate", "cas": "120-51-4", "typical_pct": (1, 8)},
    {"name": "Cinnamaldehyde", "cas": "104-55-2", "typical_pct": (0.5, 6)},
    {"name": "Farnesol", "cas": "4602-84-0", "typical_pct": (0.5, 4)},
    {"name": "Methyl Eugenol", "cas": "93-15-2", "typical_pct": (0.1, 2)},
    {"name": "Isoeugenol", "cas": "97-54-1", "typical_pct": (0.1, 3)},
]

# Impurities (always low percentage)
IMPURITIES = [
    {"name": "Myrcene", "cas": "123-35-3"},
    {"name": "Para-Cymene", "cas": "99-87-6"},
    {"name": "Camphene", "cas": "79-92-5"},
    {"name": "Terpinolene", "cas": "586-62-9"},
    {"name": "Ocimene", "cas": "13877-91-3"},
]

# Materials (fragrances and essential oils)
MATERIALS = [
    {"ref": "LEM-001", "name": "Lemon Oil Italy", "type": "NATURAL", "supplier": "Citrus Italy SpA"},
    {"ref": "ORN-002", "name": "Orange Oil Brazil", "type": "NATURAL", "supplier": "Brasil Citrus Ltd"},
    {"ref": "LAV-003", "name": "Lavender Oil France", "type": "NATURAL", "supplier": "Provence Essences"},
    {"ref": "PEP-004", "name": "Peppermint Oil USA", "type": "NATURAL", "supplier": "American Mint Co"},
    {"ref": "EUC-005", "name": "Eucalyptus Oil Australia", "type": "NATURAL", "supplier": "Aussie Oils Pty"},
    {"ref": "ROS-006", "name": "Rose Oil Bulgaria", "type": "NATURAL", "supplier": "Bulgarian Rose SA"},
    {"ref": "VAN-007", "name": "Vanilla Extract Madagascar", "type": "NATURAL", "supplier": "Madagascar Vanilla"},
    {"ref": "CIN-008", "name": "Cinnamon Bark Oil Ceylon", "type": "NATURAL", "supplier": "Ceylon Spices"},
    {"ref": "SAN-009", "name": "Sandalwood Oil India", "type": "NATURAL", "supplier": "Indian Essentials"},
    {"ref": "BER-010", "name": "Bergamot Oil Italy", "type": "NATURAL", "supplier": "Citrus Italy SpA"},
    {"ref": "GER-011", "name": "Geranium Oil Egypt", "type": "NATURAL", "supplier": "Egyptian Flowers"},
    {"ref": "JAS-012", "name": "Jasmine Absolute India", "type": "NATURAL", "supplier": "Indian Essentials"},
    {"ref": "LIM-S01", "name": "Limonene Synthetic", "type": "SYNTHETIC", "supplier": "ChemFragrance GmbH"},
    {"ref": "LIN-S02", "name": "Linalool Synthetic", "type": "SYNTHETIC", "supplier": "ChemFragrance GmbH"},
    {"ref": "CIT-S03", "name": "Citral Synthetic", "type": "SYNTHETIC", "supplier": "Aroma Chemicals SA"},
]


def create_users(db):
    """Create dummy users"""
    print("Creating users...")
    
    users = [
        User(
            email="admin@lluchregulation.com",
            username="admin",
            full_name="Administrator",
            hashed_password=pwd_context.hash("admin123"),
            role=UserRole.ADMIN
        ),
        User(
            email="tech1@lluchregulation.com",
            username="tech_maria",
            full_name="Maria García",
            hashed_password=pwd_context.hash("tech123"),
            role=UserRole.TECHNICIAN
        ),
        User(
            email="tech2@lluchregulation.com",
            username="tech_juan",
            full_name="Juan Martínez",
            hashed_password=pwd_context.hash("tech123"),
            role=UserRole.TECHNICIAN
        ),
        User(
            email="viewer@lluchregulation.com",
            username="viewer",
            full_name="Viewer User",
            hashed_password=pwd_context.hash("viewer123"),
            role=UserRole.VIEWER
        ),
    ]
    
    for user in users:
        db.add(user)
    
    db.commit()
    print(f"Created {len(users)} users")
    return users


def create_materials(db):
    """Create dummy materials"""
    print("Creating materials...")
    
    materials = []
    for mat_data in MATERIALS:
        material = Material(
            reference_code=mat_data["ref"],
            name=mat_data["name"],
            supplier=mat_data["supplier"],
            material_type=mat_data["type"],
            description=f"High quality {mat_data['name'].lower()} for fragrance applications",
            is_active=True
        )
        materials.append(material)
        db.add(material)
    
    db.commit()
    print(f"Created {len(materials)} materials")
    return materials


def generate_csv_analysis(material, batch_num, output_dir):
    """Generate a dummy CSV chromatographic analysis file"""
    
    # Select random components for this material
    num_components = random.randint(4, 8)
    selected_components = random.sample(FRAGRANCE_COMPONENTS, num_components)
    
    # Generate percentages
    components_data = []
    total_pct = 0
    
    for comp in selected_components:
        min_pct, max_pct = comp["typical_pct"]
        pct = random.uniform(min_pct, max_pct)
        components_data.append({
            "CAS Number": comp["cas"],
            "Component": comp["name"],
            "Percentage": round(pct, 2)
        })
        total_pct += pct
    
    # Add some impurities
    num_impurities = random.randint(1, 3)
    selected_impurities = random.sample(IMPURITIES, num_impurities)
    
    for imp in selected_impurities:
        pct = random.uniform(0.05, 0.8)
        components_data.append({
            "CAS Number": imp["cas"],
            "Component": imp["name"],
            "Percentage": round(pct, 2)
        })
        total_pct += pct
    
    # Normalize to 100%
    normalization_factor = 100.0 / total_pct
    for comp in components_data:
        comp["Percentage"] = round(comp["Percentage"] * normalization_factor, 2)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(components_data)
    
    filename = f"{material.reference_code}_batch_{batch_num}.csv"
    filepath = Path(output_dir) / filename
    df.to_csv(filepath, index=False)
    
    return filepath, components_data


def create_chromatographic_analyses(db, materials, output_dir):
    """Create dummy chromatographic analyses with CSV files"""
    print("Creating chromatographic analyses...")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    analyses = []
    suppliers = ["Supplier A", "Supplier B", "Supplier C"]
    technicians = ["Dr. Ana López", "Dr. Carlos Ruiz", "Dr. Elena Fernández"]
    
    # Create 2-4 analyses per material
    for material in materials[:12]:  # First 12 materials (natural ones mainly)
        num_analyses = random.randint(2, 4)
        
        for i in range(num_analyses):
            batch_num = f"B{random.randint(1000, 9999)}"
            
            # Generate CSV file
            filepath, parsed_components = generate_csv_analysis(material, batch_num, output_dir)
            
            # Create analysis record
            analysis_date = datetime.now() - timedelta(days=random.randint(30, 365))
            
            analysis = ChromatographicAnalysis(
                material_id=material.id,
                filename=filepath.name,
                file_path=str(filepath),
                batch_number=batch_num,
                supplier=random.choice(suppliers),
                analysis_date=analysis_date,
                lab_technician=random.choice(technicians),
                weight=random.uniform(0.8, 1.5),
                parsed_data={
                    "components": [
                        {
                            "cas_number": c["CAS Number"],
                            "component_name": c["Component"],
                            "percentage": c["Percentage"],
                            "component_type": "IMPURITY" if c["Percentage"] < 1.0 else "COMPONENT"
                        }
                        for c in parsed_components
                    ],
                    "total_percentage": 100.0,
                    "component_count": len(parsed_components),
                    "validation_errors": [],
                    "success": True
                },
                is_processed=1,
                processing_notes="Successfully parsed"
            )
            
            analyses.append(analysis)
            db.add(analysis)
    
    db.commit()
    print(f"Created {len(analyses)} chromatographic analyses with CSV files")
    return analyses


def create_composites(db, materials, analyses):
    """Create dummy composites from analyses"""
    print("Creating composites...")
    
    from app.services.composite_calculator import CompositeCalculator
    
    calculator = CompositeCalculator(db)
    composites = []
    
    # Create composites for materials that have analyses
    material_ids_with_analyses = set(a.material_id for a in analyses)
    
    for material_id in material_ids_with_analyses:
        # Create 1-2 composite versions
        num_versions = random.randint(1, 2)
        
        for version_num in range(num_versions):
            # Get subset of analyses for this version
            material_analyses = [a for a in analyses if a.material_id == material_id]
            
            if version_num == 0:
                # First version: use all analyses
                selected_analyses = material_analyses
            else:
                # Second version: use random subset
                selected_analyses = random.sample(
                    material_analyses, 
                    random.randint(2, len(material_analyses))
                )
            
            try:
                composite = calculator.calculate_from_lab_analyses(
                    material_id=material_id,
                    analysis_ids=[a.id for a in selected_analyses],
                    notes=f"Version {version_num + 1} - Generated from {len(selected_analyses)} analyses"
                )
                
                # Set random status
                if version_num == 0 and num_versions > 1:
                    # Older version is approved
                    composite.status = CompositeStatus.APPROVED
                    composite.approved_at = datetime.now() - timedelta(days=random.randint(60, 180))
                else:
                    # Latest version varies
                    status_choice = random.choice([
                        CompositeStatus.APPROVED,
                        CompositeStatus.APPROVED,
                        CompositeStatus.PENDING_APPROVAL,
                        CompositeStatus.DRAFT
                    ])
                    composite.status = status_choice
                    if status_choice == CompositeStatus.APPROVED:
                        composite.approved_at = datetime.now() - timedelta(days=random.randint(1, 60))
                
                composites.append(composite)
                db.add(composite)
                
            except Exception as e:
                print(f"Error creating composite for material {material_id}: {e}")
    
    db.commit()
    print(f"Created {len(composites)} composites")
    return composites


def main():
    """Main function to generate all dummy data"""
    print("=" * 60)
    print("Generating Dummy Data for Lluch Regulation System")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Clear existing data (optional)
        if "--clean" in sys.argv:
            print("\nCleaning existing data...")
            db.query(ApprovalWorkflow).delete()
            db.query(CompositeComponent).delete()
            db.query(Composite).delete()
            db.query(ChromatographicAnalysis).delete()
            db.query(Material).delete()
            db.query(User).delete()
            db.commit()
            print("Existing data cleared")
        
        # Determine upload directory
        upload_dir = "../data/uploads"
        if not os.path.exists(upload_dir):
            upload_dir = "data/uploads"
        
        # Create data
        users = create_users(db)
        materials = create_materials(db)
        analyses = create_chromatographic_analyses(db, materials, upload_dir)
        composites = create_composites(db, materials, analyses)
        
        print("\n" + "=" * 60)
        print("Dummy Data Generation Complete!")
        print("=" * 60)
        print(f"Users created: {len(users)}")
        print(f"Materials created: {len(materials)}")
        print(f"Chromatographic analyses created: {len(analyses)}")
        print(f"Composites created: {len(composites)}")
        print("\nDefault login credentials:")
        print("  Admin: admin / admin123")
        print("  Technician: tech_maria / tech123")
        print("  Viewer: viewer / viewer123")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError generating dummy data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()






