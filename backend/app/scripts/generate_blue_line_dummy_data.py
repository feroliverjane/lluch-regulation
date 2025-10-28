"""
Script to generate dummy data for Blue Line testing
Creates synchronized data: Materials → Composites → Approvals → Blue Lines
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.material import Material
from app.models.composite import Composite, CompositeComponent, CompositeOrigin, CompositeStatus, ComponentType
from app.models.approval_workflow import ApprovalWorkflow, WorkflowStatus
from app.models.user import User, UserRole
from app.models.blue_line import BlueLine, BlueLineMaterialType, BlueLineSyncStatus
from app.models.blue_line_field_logic import BlueLineFieldLogic
from app.models.chromatographic_analysis import ChromatographicAnalysis
import asyncio


def create_sample_field_logics(db: Session):
    """Create sample field logic configurations for testing"""
    print("Creating sample field logic configurations...")
    
    field_logics = [
        {
            "field_name": "material_reference",
            "field_label": "Código de Referencia del Material",
            "field_category": "Información Básica",
            "field_type": "text",
            "material_type_filter": "ALL",
            "logic_expression": {"source": "material.reference_code"},
            "priority": 1,
            "is_active": True,
            "description": "Código de referencia del material",
            "example_value": "LEM-001"
        },
        {
            "field_name": "material_name",
            "field_label": "Nombre del Material",
            "field_category": "Información Básica",
            "field_type": "text",
            "material_type_filter": "ALL",
            "logic_expression": {"source": "material.name"},
            "priority": 2,
            "is_active": True,
            "description": "Nombre completo del material",
            "example_value": "Lemon Essential Oil"
        },
        {
            "field_name": "supplier_code",
            "field_label": "Código del Proveedor",
            "field_category": "Proveedor",
            "field_type": "text",
            "material_type_filter": "ALL",
            "logic_expression": {"source": "supplier_code"},
            "priority": 3,
            "is_active": True,
            "description": "Código del proveedor LLUCH",
            "example_value": "PROV-001"
        },
        {
            "field_name": "lluch_reference",
            "field_label": "Referencia LLUCH",
            "field_category": "Información Básica",
            "field_type": "text",
            "material_type_filter": "ALL",
            "logic_expression": {"source": "material.lluch_reference"},
            "priority": 4,
            "is_active": True,
            "description": "Referencia LLUCH 103721",
            "example_value": "LLUCH-103721-001"
        },
        {
            "field_name": "cas_number",
            "field_label": "Número CAS",
            "field_category": "Información Química",
            "field_type": "text",
            "material_type_filter": "ALL",
            "logic_expression": {"source": "material.cas_number"},
            "priority": 5,
            "is_active": True,
            "description": "Número CAS del material",
            "example_value": "8008-56-8"
        },
        {
            "field_name": "material_type_code",
            "field_label": "Tipo de Material (SAP)",
            "field_category": "Clasificación",
            "field_type": "text",
            "material_type_filter": "ALL",
            "logic_expression": {"source": "material.sap_status"},
            "priority": 6,
            "is_active": True,
            "description": "Código de tipo de material en SAP",
            "example_value": "Z1"
        },
        {
            "field_name": "composite_count",
            "field_label": "Cantidad de Composites",
            "field_category": "Análisis",
            "field_type": "number",
            "material_type_filter": "ALL",
            "logic_expression": {"calculation": {"type": "count", "source": "composites"}},
            "priority": 10,
            "is_active": True,
            "description": "Número total de composites aprobados",
            "example_value": "3"
        },
        {
            "field_name": "main_components",
            "field_label": "Componentes Principales",
            "field_category": "Composición",
            "field_type": "calculated",
            "material_type_filter": "Z002",
            "logic_expression": {"calculation": {"type": "list", "source": "composite.components"}},
            "priority": 20,
            "is_active": True,
            "description": "Lista de componentes principales del último composite",
            "example_value": "[{name: 'Limonene', percentage: 95.2}]"
        },
        {
            "field_name": "supplier_name",
            "field_label": "Nombre del Proveedor",
            "field_category": "Proveedor",
            "field_type": "text",
            "material_type_filter": "ALL",
            "logic_expression": {"source": "material.supplier"},
            "priority": 7,
            "is_active": True,
            "description": "Nombre del proveedor",
            "example_value": "Citrus Suppliers Inc."
        },
        {
            "field_name": "lluch_company",
            "field_label": "Empresa",
            "field_category": "Información Básica",
            "field_type": "text",
            "material_type_filter": "ALL",
            "logic_expression": {"fixed_value": "LLUCH"},
            "priority": 0,
            "is_active": True,
            "description": "Empresa propietaria (siempre LLUCH)",
            "example_value": "LLUCH"
        }
    ]
    
    created_count = 0
    for logic_data in field_logics:
        existing = db.query(BlueLineFieldLogic).filter(
            BlueLineFieldLogic.field_name == logic_data["field_name"]
        ).first()
        
        if not existing:
            field_logic = BlueLineFieldLogic(**logic_data)
            db.add(field_logic)
            created_count += 1
    
    db.commit()
    print(f"✅ Created {created_count} field logic configurations")


def create_materials_with_blue_line_fields(db: Session):
    """Create materials with proper Blue Line fields"""
    print("Creating materials with Blue Line fields...")
    
    materials_data = [
        {
            "reference_code": "LEM-001",
            "name": "Lemon Essential Oil - Sicily",
            "supplier": "Citrus Masters Ltd",
            "supplier_code": "PROV-CITRUS-001",
            "sap_status": "Z1",  # Active/validated - will sync TO SAP
            "lluch_reference": "LLUCH-103721-LEM001",
            "cas_number": "8008-56-8",
            "material_type": "NATURAL",
            "last_purchase_date": datetime.now() - timedelta(days=45),
            "is_blue_line_eligible": True
        },
        {
            "reference_code": "LAV-003",
            "name": "Lavender Oil - Provence",
            "supplier": "Lavender Fields SA",
            "supplier_code": "PROV-LAV-003",
            "sap_status": "Z1",
            "lluch_reference": "LLUCH-103721-LAV003",
            "cas_number": "8000-28-0",
            "material_type": "NATURAL",
            "last_purchase_date": datetime.now() - timedelta(days=120),
            "is_blue_line_eligible": True
        },
        {
            "reference_code": "PEP-004",
            "name": "Peppermint Oil - USA",
            "supplier": "American Mint Co",
            "supplier_code": "PROV-MINT-004",
            "sap_status": "Z2",  # Provisional - will import FROM SAP
            "lluch_reference": "LLUCH-103721-PEP004",
            "cas_number": "8006-90-4",
            "material_type": "NATURAL",
            "last_purchase_date": datetime.now() - timedelta(days=200),
            "is_blue_line_eligible": True
        },
        {
            "reference_code": "EUC-005",
            "name": "Eucalyptus Oil - Australia",
            "supplier": "Eucalyptus Global",
            "supplier_code": "PROV-EUC-005",
            "sap_status": "Z1",
            "lluch_reference": "LLUCH-103721-EUC005",
            "cas_number": "8000-48-4",
            "material_type": "NATURAL",
            "last_purchase_date": datetime.now() - timedelta(days=30),
            "is_blue_line_eligible": True
        },
        {
            "reference_code": "ROS-006",
            "name": "Rose Oil - Bulgaria",
            "supplier": "Bulgarian Rose Ltd",
            "supplier_code": "PROV-ROSE-006",
            "sap_status": "Z1",
            "lluch_reference": "LLUCH-103721-ROS006",
            "cas_number": "8007-01-0",
            "material_type": "NATURAL",
            "last_purchase_date": datetime.now() - timedelta(days=90),
            "is_blue_line_eligible": True
        },
        {
            "reference_code": "VAN-007",
            "name": "Vanilla Extract - Madagascar",
            "supplier": "Vanilla Traders Inc",
            "supplier_code": "PROV-VAN-007",
            "sap_status": "Z1",
            "lluch_reference": "LLUCH-103721-VAN007",
            "cas_number": "8024-06-4",
            "material_type": "NATURAL",
            "last_purchase_date": datetime.now() - timedelta(days=60),
            "is_blue_line_eligible": True
        }
    ]
    
    materials = []
    for mat_data in materials_data:
        existing = db.query(Material).filter(
            Material.reference_code == mat_data["reference_code"]
        ).first()
        
        if existing:
            # Update existing
            for key, value in mat_data.items():
                setattr(existing, key, value)
            materials.append(existing)
        else:
            # Create new
            material = Material(**mat_data)
            db.add(material)
            materials.append(material)
    
    db.commit()
    for m in materials:
        db.refresh(m)
    
    print(f"✅ Created/updated {len(materials)} materials with Blue Line fields")
    return materials


def create_composites_and_approvals(db: Session, materials: list):
    """Create composites with proper approvals"""
    print("Creating composites and approval workflows...")
    
    # Get or create a technician user
    technician = db.query(User).filter(User.username == "tech_maria").first()
    if not technician:
        technician = User(
            username="tech_maria",
            email="maria@lluch.com",
            full_name="Maria Technical",
            role=UserRole.TECHNICIAN,
            hashed_password="hashed_tech123"
        )
        db.add(technician)
        db.commit()
        db.refresh(technician)
    
    composites_created = 0
    approvals_created = 0
    
    # First create LAB composites for first 4 materials (will be Z002 type)
    for material in materials[:4]:
        # Create chromatographic analysis
        analysis = ChromatographicAnalysis(
            material_id=material.id,
            filename=f"{material.reference_code}_analysis.csv",
            file_path=f"data/uploads/{material.reference_code}_analysis.csv",
            batch_number=f"BATCH-{material.reference_code}-2024",
            supplier=material.supplier,
            analysis_date=datetime.now() - timedelta(days=60),
            lab_technician="Maria Lopez",
            weight=100.0,
            is_processed=1,
            parsed_data={
                "components": [
                    {"cas_number": material.cas_number, "component_name": f"{material.name.split()[0]} Main Component", "percentage": 92.5, "component_type": "COMPONENT"},
                    {"cas_number": "000-00-1", "component_name": "Component A", "percentage": 5.2, "component_type": "COMPONENT"},
                    {"cas_number": "000-00-2", "component_name": "Impurity B", "percentage": 2.3, "component_type": "IMPURITY"}
                ]
            }
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Create composite
        composite = Composite(
            material_id=material.id,
            version=1,
            origin=CompositeOrigin.LAB,
            status=CompositeStatus.APPROVED,
            approved_at=datetime.now() - timedelta(days=30),
            composite_metadata={
                "analysis_ids": [analysis.id],
                "batches": [analysis.batch_number],
                "suppliers": [material.supplier],
                "calculation_method": "lab_analysis"
            },
            notes=f"Composite aprobado para {material.name}"
        )
        db.add(composite)
        db.commit()
        db.refresh(composite)
        
        # Add components
        components_data = [
            {
                "component_name": f"{material.name.split()[0]} Main Component",
                "cas_number": material.cas_number,
                "percentage": 92.5,
                "component_type": ComponentType.COMPONENT,
                "confidence_level": 95.0
            },
            {
                "component_name": "Component A",
                "cas_number": "000-00-1",
                "percentage": 5.2,
                "component_type": ComponentType.COMPONENT,
                "confidence_level": 88.0
            },
            {
                "component_name": "Impurity B",
                "cas_number": "000-00-2",
                "percentage": 2.3,
                "component_type": ComponentType.IMPURITY,
                "confidence_level": 75.0
            }
        ]
        
        for comp_data in components_data:
            component = CompositeComponent(
                composite_id=composite.id,
                **comp_data
            )
            db.add(component)
        
        composites_created += 1
        
        # Create approval workflow with Blue Line states
        # Alternate between different approval scenarios
        if material.reference_code in ["LEM-001", "LAV-003", "EUC-005"]:
            # APC in Regulatory (Approved Conditionally)
            workflow = ApprovalWorkflow(
                composite_id=composite.id,
                assigned_to_id=technician.id,
                status=WorkflowStatus.APC,
                section="Regulatory",
                regulatory_status="APC",  # Approved Conditionally in Regulatory
                technical_status="APPROVED",  # No rejection in Technical
                review_comments="Material cumple con especificaciones regulatorias condicionalmente",
                assigned_at=datetime.now() - timedelta(days=35),
                reviewed_at=datetime.now() - timedelta(days=30),
                completed_at=datetime.now() - timedelta(days=30)
            )
        else:
            # APR in Regulatory (Approved Regulatory)
            workflow = ApprovalWorkflow(
                composite_id=composite.id,
                assigned_to_id=technician.id,
                status=WorkflowStatus.APR,
                section="Regulatory",
                regulatory_status="APR",  # Approved Regulatory
                technical_status="APPROVED",
                review_comments="Material totalmente aprobado para uso regulatorio",
                assigned_at=datetime.now() - timedelta(days=35),
                reviewed_at=datetime.now() - timedelta(days=30),
                completed_at=datetime.now() - timedelta(days=30)
            )
        
        db.add(workflow)
        approvals_created += 1
    
    # Create CALCULATED composite for VAN-007 (will be Z001 type - no LAB analysis)
    vanilla_material = next((m for m in materials if m.reference_code == "VAN-007"), None)
    if vanilla_material:
        # Create a CALCULATED composite (from supplier documentation, not LAB)
        vanilla_composite = Composite(
            material_id=vanilla_material.id,
            version=1,
            origin=CompositeOrigin.CALCULATED,  # NOT LAB - will result in Z001
            status=CompositeStatus.APPROVED,
            approved_at=datetime.now() - timedelta(days=20),
            composite_metadata={
                "source": "supplier_documentation",
                "calculation_method": "document_based",
                "notes": "Basado en documentación técnica del proveedor"
            },
            notes="Composite calculado a partir de ficha técnica del proveedor (sin análisis LAB)"
        )
        db.add(vanilla_composite)
        db.commit()
        db.refresh(vanilla_composite)
        
        # Add components from supplier documentation (worst case scenario)
        vanilla_components = [
            {
                "component_name": "Vanillin",
                "cas_number": "121-33-5",
                "percentage": 2.5,  # Minimum expected
                "component_type": ComponentType.COMPONENT,
                "notes": "Worst case from supplier spec"
            },
            {
                "component_name": "p-Hydroxybenzaldehyde",
                "cas_number": "123-08-0",
                "percentage": 1.8,
                "component_type": ComponentType.COMPONENT,
                "notes": "Worst case from supplier spec"
            },
            {
                "component_name": "Other compounds",
                "cas_number": None,
                "percentage": 95.7,
                "component_type": ComponentType.COMPONENT,
                "notes": "Alcohol and other extractives"
            }
        ]
        
        for comp_data in vanilla_components:
            component = CompositeComponent(
                composite_id=vanilla_composite.id,
                **comp_data
            )
            db.add(component)
        
        composites_created += 1
        
        # Create approval for vanilla
        vanilla_workflow = ApprovalWorkflow(
            composite_id=vanilla_composite.id,
            assigned_to_id=technician.id,
            status=WorkflowStatus.APR,
            section="Regulatory",
            regulatory_status="APR",
            technical_status="APPROVED",
            review_comments="Material aprobado basado en documentación técnica del proveedor",
            assigned_at=datetime.now() - timedelta(days=25),
            reviewed_at=datetime.now() - timedelta(days=20),
            completed_at=datetime.now() - timedelta(days=20)
        )
        db.add(vanilla_workflow)
        approvals_created += 1
    
    db.commit()
    print(f"✅ Created {composites_created} composites (LAB + CALCULATED) and {approvals_created} approval workflows")


async def generate_blue_lines(db: Session, materials: list):
    """Generate Blue Lines for eligible materials"""
    print("Generating Blue Lines...")
    
    from app.services.blue_line_calculator import BlueLineCalculator
    
    calculator = BlueLineCalculator(db)
    blue_lines_created = 0
    
    for material in materials[:5]:  # First 5 have composites and approvals (4 LAB + 1 CALCULATED)
        if material.supplier_code and material.is_blue_line_eligible:
            try:
                blue_line = await calculator.calculate_blue_line(
                    material_id=material.id,
                    supplier_code=material.supplier_code,
                    force_recalculate=True
                )
                
                if blue_line:
                    # For Z1 materials, mark as synced (simulating successful sync)
                    if material.sap_status == "Z1":
                        blue_line.sync_status = BlueLineSyncStatus.SYNCED
                        blue_line.last_synced_at = datetime.now() - timedelta(hours=2)
                    
                    blue_lines_created += 1
                    print(f"  ✓ Blue Line created for {material.reference_code} (Type: {blue_line.material_type}, Sync: {blue_line.sync_status})")
                else:
                    print(f"  ✗ Not eligible: {material.reference_code}")
            
            except Exception as e:
                print(f"  ✗ Error for {material.reference_code}: {e}")
    
    db.commit()
    print(f"✅ Generated {blue_lines_created} Blue Lines")


def main():
    """Main function to generate all Blue Line dummy data"""
    print("\n" + "="*70)
    print("🔵 GENERANDO DATOS DUMMY PARA LÍNEA AZUL")
    print("="*70 + "\n")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Step 1: Create field logic configurations
        create_sample_field_logics(db)
        print()
        
        # Step 2: Create materials with Blue Line fields
        materials = create_materials_with_blue_line_fields(db)
        print()
        
        # Step 3: Create composites and approval workflows
        create_composites_and_approvals(db, materials)
        print()
        
        # Step 4: Generate Blue Lines
        asyncio.run(generate_blue_lines(db, materials))
        print()
        
        print("="*70)
        print("✅ DATOS DUMMY GENERADOS EXITOSAMENTE")
        print("="*70)
        print("\n📊 Resumen:")
        print(f"  • Materiales: {len(materials)}")
        print(f"  • Field Logics: {db.query(BlueLineFieldLogic).count()}")
        print(f"  • Composites: {db.query(Composite).count()}")
        print(f"  • Approval Workflows: {db.query(ApprovalWorkflow).count()}")
        print(f"  • Blue Lines: {db.query(BlueLine).count()}")
        print("\n🌐 Acceso:")
        print("  • Backend API: http://localhost:8000/api/blue-line")
        print("  • API Docs: http://localhost:8000/docs")
        print("  • Frontend: http://localhost:5173/blue-line")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

