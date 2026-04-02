# test_reservacion_emails.py
"""Script de prueba para verificar que los correos de reservación se forman correctamente"""

from services.email_service import enviar_confirmacion_reservacion, enviar_confirmacion_estado_reservacion

print("=" * 70)
print("TEST: Envío de Correos de Reservación")
print("=" * 70)

# Test 1: Confirmación de nueva reservación
print("\n1. Probando función de confirmación de nueva reservación...")
try:
    success, msg = enviar_confirmacion_reservacion(
        correo_destino="test@example.com",
        nombre="Juan Pérez",
        email="test@example.com",
        telefono="+52 (555) 123-4567",
        numero_personas="4",
        fecha="2026-04-15",
        hora="19:30",
        notas="Mesa cerca de la ventana por favor"
    )
    print(f"   ✅ Resultado: {msg}" if success else f"   ❌ Error: {msg}")
except Exception as e:
    print(f"   ❌ Excepción: {e}")

# Test 2: Confirmación de cambio de estado a confirmada
print("\n2. Probando función de confirmación de estado (CONFIRMADA)...")
try:
    success, msg = enviar_confirmacion_estado_reservacion(
        correo_destino="test@example.com",
        nombre="Juan Pérez",
        nuevo_estado="confirmada",
        fecha="2026-04-15",
        hora="19:30",
        numero_personas="4"
    )
    print(f"   ✅ Resultado: {msg}" if success else f"   ❌ Error: {msg}")
except Exception as e:
    print(f"   ❌ Excepción: {e}")

# Test 3: Confirmación de cambio de estado a cancelada
print("\n3. Probando función de confirmación de estado (CANCELADA)...")
try:
    success, msg = enviar_confirmacion_estado_reservacion(
        correo_destino="test@example.com",
        nombre="Juan Pérez",
        nuevo_estado="cancelada",
        fecha="2026-04-15",
        hora="19:30",
        numero_personas="4"
    )
    print(f"   ✅ Resultado: {msg}" if success else f"   ❌ Error: {msg}")
except Exception as e:
    print(f"   ❌ Excepción: {e}")

print("\n" + "=" * 70)
print("Pruebas completadas")
print("=" * 70)
