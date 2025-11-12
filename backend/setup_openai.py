#!/usr/bin/env python3
"""
Script interactivo para configurar OpenAI API
Ejecuta: python setup_openai.py
"""

import os
from pathlib import Path

def main():
    print("="*80)
    print("  🔧 CONFIGURACIÓN DE OPENAI API")
    print("="*80)
    print()
    
    # Encontrar archivo .env
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print("⚠️  Archivo .env no encontrado")
        crear = input("¿Crear nuevo archivo .env? (s/n): ").lower()
        if crear == 's':
            env_path.touch()
            print("✅ Archivo .env creado")
        else:
            print("❌ Necesitas un archivo .env para continuar")
            return
    
    # Leer .env actual
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Mostrar configuración actual
    print("\n📋 Configuración actual:")
    current_key = env_vars.get('OPENAI_API_KEY', '')
    use_openai = env_vars.get('USE_OPENAI_FOR_EXTRACTION', 'false').lower() == 'true'
    
    if current_key:
        masked_key = current_key[:7] + "..." + current_key[-4:] if len(current_key) > 11 else "***"
        print(f"   OPENAI_API_KEY: {masked_key}")
    else:
        print("   OPENAI_API_KEY: (no configurado)")
    
    print(f"   USE_OPENAI_FOR_EXTRACTION: {use_openai}")
    
    # Obtener API key
    print("\n" + "="*80)
    print("🔑 PASO 1: Obtener API Key de OpenAI")
    print("="*80)
    print()
    print("1. Ve a: https://platform.openai.com/api-keys")
    print("2. Inicia sesión o crea una cuenta")
    print("3. Click en 'Create new secret key'")
    print("4. Copia la key (solo se muestra una vez)")
    print()
    
    action = input("¿Ya tienes tu API key? (s/n): ").lower()
    
    if action != 's':
        print("\n💡 Abre este enlace para obtener tu API key:")
        print("   https://platform.openai.com/api-keys")
        print("\nCuando la tengas, ejecuta este script de nuevo.")
        return
    
    api_key = input("\nPega tu API key aquí (sk-...): ").strip()
    
    if not api_key.startswith('sk-'):
        print("⚠️  La API key debería empezar con 'sk-'")
        confirm = input("¿Continuar de todas formas? (s/n): ").lower()
        if confirm != 's':
            return
    
    # Preguntar si activar
    print("\n" + "="*80)
    print("⚙️  PASO 2: Activar OpenAI")
    print("="*80)
    print()
    print("¿Quieres activar OpenAI para extracción de PDFs ahora?")
    print("  - Si = Usa OpenAI (más preciso, ~$0.01-0.03 por PDF)")
    print("  - No = Usa OCR local (gratis, menos preciso)")
    print()
    
    activar = input("Activar OpenAI? (s/n): ").lower()
    use_openai = activar == 's'
    
    # Actualizar .env
    print("\n" + "="*80)
    print("💾 Guardando configuración...")
    print("="*80)
    
    # Leer todas las líneas
    lines = []
    openai_key_written = False
    use_openai_written = False
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('OPENAI_API_KEY='):
                    lines.append(f"OPENAI_API_KEY={api_key}\n")
                    openai_key_written = True
                elif stripped.startswith('USE_OPENAI_FOR_EXTRACTION='):
                    lines.append(f"USE_OPENAI_FOR_EXTRACTION={str(use_openai).lower()}\n")
                    use_openai_written = True
                else:
                    lines.append(line)
    
    # Agregar si no existían
    if not openai_key_written:
        lines.append(f"\n# OpenAI API Configuration\n")
        lines.append(f"OPENAI_API_KEY={api_key}\n")
    
    if not use_openai_written:
        lines.append(f"USE_OPENAI_FOR_EXTRACTION={str(use_openai).lower()}\n")
    
    # Escribir de vuelta
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print("✅ Configuración guardada en .env")
    
    # Verificar
    print("\n" + "="*80)
    print("🧪 Verificando configuración...")
    print("="*80)
    
    try:
        from app.core.config import settings
        print(f"✅ Config cargado correctamente")
        print(f"✅ OPENAI_API_KEY: {'Configurado' if settings.OPENAI_API_KEY else 'No configurado'}")
        print(f"✅ USE_OPENAI_FOR_EXTRACTION: {settings.USE_OPENAI_FOR_EXTRACTION}")
        
        if settings.OPENAI_API_KEY and settings.USE_OPENAI_FOR_EXTRACTION:
            print("\n🎉 ¡OpenAI está ACTIVADO!")
            print("   El sistema usará OpenAI Vision API para extraer PDFs")
        elif settings.OPENAI_API_KEY:
            print("\n⚠️  OpenAI API key configurada pero NO activada")
            print("   Cambia USE_OPENAI_FOR_EXTRACTION=true para activarla")
        else:
            print("\n⚠️  OpenAI no está configurado")
            
    except Exception as e:
        print(f"⚠️  Error verificando: {e}")
    
    # Instrucciones finales
    print("\n" + "="*80)
    print("📚 Próximos Pasos")
    print("="*80)
    print()
    print("1. Reinicia el servidor backend para que cargue la nueva configuración")
    print("2. Prueba subiendo un PDF y extrayendo composite")
    print("3. El sistema usará OpenAI automáticamente si está activado")
    print()
    print("💡 Para probar:")
    print("   python test_openai_extraction.py path/to/test.pdf")
    print()
    print("📖 Más información en: CONFIGURAR_OPENAI.md")
    print("="*80)

if __name__ == "__main__":
    main()












