#!/usr/bin/env python3
"""
Script de ejemplo para el Sistema de Gestión de Composites
Lluch Regulation

Ejecutar: python3 ejemplo_uso.py
"""

import urllib.request
import json
from typing import Dict, Any


API_URL = "http://localhost:8000/api"


def hacer_peticion(endpoint: str, metodo: str = "GET", datos: Dict = None) -> Any:
    """Función helper para hacer peticiones a la API"""
    url = f"{API_URL}{endpoint}"
    
    if metodo == "GET":
        response = urllib.request.urlopen(url)
        return json.loads(response.read())
    elif metodo == "POST":
        req = urllib.request.Request(
            url,
            data=json.dumps(datos).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req)
        return json.loads(response.read())


def ejemplo_1_listar_materiales():
    """Ejemplo 1: Listar todos los materiales"""
    print("\n" + "="*60)
    print("EJEMPLO 1: Listar todos los materiales")
    print("="*60)
    
    materiales = hacer_peticion("/materials")
    
    print(f"\nTotal de materiales: {len(materiales)}")
    print("\nListado:")
    for material in materiales:
        print(f"  • {material['reference_code']}: {material['name']}")
        print(f"    Proveedor: {material['supplier']}")
        print(f"    Tipo: {material['material_type']}")
        print()


def ejemplo_2_ver_material_detalle():
    """Ejemplo 2: Ver detalle de un material específico"""
    print("\n" + "="*60)
    print("EJEMPLO 2: Ver detalle del material LEM-001")
    print("="*60)
    
    material = hacer_peticion("/materials/1")
    
    print(f"\nReferencia: {material['reference_code']}")
    print(f"Nombre: {material['name']}")
    print(f"Proveedor: {material['supplier']}")
    print(f"Descripción: {material['description']}")
    print(f"Tipo: {material['material_type']}")
    print(f"Activo: {'Sí' if material['is_active'] else 'No'}")


def ejemplo_3_ver_composites():
    """Ejemplo 3: Ver composites de un material"""
    print("\n" + "="*60)
    print("EJEMPLO 3: Ver composites del material 1")
    print("="*60)
    
    composites = hacer_peticion("/composites/material/1")
    
    if not composites:
        print("\nNo hay composites para este material")
        return
    
    for composite in composites:
        print(f"\n📊 Composite ID: {composite['id']}")
        print(f"   Versión: {composite['version']}")
        print(f"   Origen: {composite['origin']}")
        print(f"   Estado: {composite['status']}")
        print(f"   Componentes: {len(composite['components'])}")
        print(f"\n   Composición:")
        
        # Mostrar componentes ordenados por porcentaje
        componentes = sorted(
            composite['components'], 
            key=lambda x: x['percentage'], 
            reverse=True
        )
        
        for comp in componentes:
            tipo_emoji = "🔷" if comp['component_type'] == 'COMPONENT' else "⚠️"
            print(f"   {tipo_emoji} {comp['component_name']}: {comp['percentage']}%")
            if comp['cas_number']:
                print(f"      CAS: {comp['cas_number']}")


def ejemplo_4_crear_material():
    """Ejemplo 4: Crear un nuevo material"""
    print("\n" + "="*60)
    print("EJEMPLO 4: Crear nuevo material")
    print("="*60)
    
    nuevo_material = {
        "reference_code": "ROS-006",
        "name": "Rose Oil Bulgaria",
        "supplier": "Bulgarian Rose SA",
        "description": "Premium Bulgarian rose oil",
        "cas_number": "8007-01-0",
        "material_type": "NATURAL"
    }
    
    try:
        material_creado = hacer_peticion("/materials", "POST", nuevo_material)
        print(f"\n✅ Material creado exitosamente!")
        print(f"   ID: {material_creado['id']}")
        print(f"   Nombre: {material_creado['name']}")
        print(f"   Referencia: {material_creado['reference_code']}")
    except Exception as e:
        print(f"\n⚠️  Error al crear material: {e}")
        print("   (Puede que ya exista)")


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("   SISTEMA DE GESTIÓN DE COMPOSITES - EJEMPLOS DE USO")
    print("   Lluch Regulation")
    print("="*70)
    
    try:
        # Verificar que la API esté disponible
        hacer_peticion("/materials")
        print("\n✅ API disponible en:", API_URL)
    except Exception as e:
        print(f"\n❌ Error: No se puede conectar a la API")
        print(f"   Asegúrate de que el backend esté corriendo en {API_URL}")
        return
    
    # Ejecutar ejemplos
    ejemplo_1_listar_materiales()
    input("\nPresiona Enter para continuar...")
    
    ejemplo_2_ver_material_detalle()
    input("\nPresiona Enter para continuar...")
    
    ejemplo_3_ver_composites()
    input("\nPresiona Enter para continuar...")
    
    ejemplo_4_crear_material()
    
    print("\n" + "="*70)
    print("✅ EJEMPLOS COMPLETADOS")
    print("="*70)
    print("\nPróximos pasos:")
    print("  • Abre http://localhost:5173 para ver la interfaz web")
    print("  • Abre http://localhost:8000/docs para la documentación API")
    print("  • Lee GETTING_STARTED.md para más información")
    print()


if __name__ == "__main__":
    main()






