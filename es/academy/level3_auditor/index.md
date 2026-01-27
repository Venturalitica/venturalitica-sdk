# Nivel 3: El Auditor (Traza de Caja de Cristal) 🟠

**Objetivo**: Verificar tu política visual y criptográficamente usando el método de **Caja de Cristal**.

**Prerrequisito**: [Nivel 2 (El Integrador)](https://venturalitica.github.io/venturalitica-sdk/es/academy/level2_integrator/index.md)

______________________________________________________________________

## 1. El Problema: "Pasó, pero ¿podemos confiar en el proceso?"

En el Nivel 2, registraste el puntaje de cumplimiento. Pero para la **IA de Alto Riesgo** (como el Scoring de Crédito), las métricas no son suficientes. Un Auditor pregunta: *"¿Probaste en el dataset real, o filtraste los préstamos rechazados?"* y *"¿Puedes probar que este código fue realmente ejecutado?"*

## 2. La Solución: La Traza de "Caja de Cristal"

Según nuestros **Documentos de Auditoría Estratégica**, la auditoría profesional requiere más que resultados—requiere **Proveniencia**.

Venturalítica usa un contexto `monitor()` para registrar todo:

- **El Código**: Análisis AST de tu script.
- **Los Datos**: Conteo de filas y esquema de columnas.
- **El Hardware**: Memoria, CPU y stats de Carbono (Artículo 15).
- **El Sello**: Un hash criptográfico SHA-256 de toda la sesión.

### El Upgrade

Continuamos trabajando en el mismo proyecto. No se requiere configuración nueva.

### Ejecutar con el Monitor Nativo

Envuelve tu ejecución en `vl.monitor()`. Este context manager captura el "Handshake" entre tu código y la política cosechando metadatos físicos y lógicos.

### 🔍 Profundización: Caja de Cristal vs Caja Negra

| Característica | ⬛ Caja Negra (Estándar)           | 🪟 **Caja de Cristal (Venturalítica)**                                         |
| -------------- | ---------------------------------- | ------------------------------------------------------------------------------ |
| **Lógica**     | "Confía en mí, ejecuté el código." | **Análisis AST**: Registramos *qué* función mapeó código a política.           |
| **Datos**      | "Aquí está el CSV."                | **Huella Digital**: Registramos el SHA-256 del dataset en tiempo de ejecución. |
| **Alcance**    | Código                             | Código + Entorno + Estadísticas de Hardware                                    |

```
import venturalitica as vl
from ucimlrepo import fetch_ucirepo

# 1. Cargar Datos (Lo Real)
dataset = fetch_ucirepo(id=144)
df = dataset.data.features
df['class'] = dataset.data.targets

# 2. Iniciar el Monitor Multimodal (La Caja de Cristal)
with vl.monitor("loan_audit_v1"):
    # Este bloque ahora está siendo vigilado por el Auditor
    results = vl.enforce(
        data=df,
        target="class",       # Verificando Verdad Terrestre (Ground Truth)
        age="Attribute13",    # Mapeando Edad
        policy="data_governance.yaml"
    )
    # El archivo de traza de sesión (.venturalitica/trace_loan_audit_v1.json) 
    # probará NO solo el resultado, sino CÓMO fue computado.
```

## 3. La Verificación del "Sello Digital"

Después de ejecutar la auditoría, lanza la UI:

```
uv run venturalitica ui
```

Navega a **"Artículo 13: Transparencia"**.

### Encontrando el Hash de Evidencia

Busca el **Evidence Hash** en el dashboard. `Evidence Hash: 89fbf...`

Este hash es tu **"Sello Digital"**. Si cambias *un píxel* en el dataset o *una línea* en la política, este hash cambia. Ahora puedes probar a un regulador exactamente qué pasó durante la auditoría.

## 4. El Mapa de Cumplimiento

El Dashboard traduce la evidencia JSON al lenguaje de la **EU AI Act**.

| Ley        | Pestaña del Dashboard | Qué Responder                                      |
| ---------- | --------------------- | -------------------------------------------------- |
| **Art 9**  | Gestión de Riesgos    | "¿Verificamos sesgo < 0.1?" (Tu Política)          |
| **Art 10** | Gobernanza de Datos   | "¿Son los datos de entrenamiento representativos?" |
| **Art 13** | Transparencia         | "¿Qué librerías (BOM) estamos usando?"             |

## 5. Mensajes para Llevar a Casa 🏠

1. **No Confíes, Verifica**: El **Archivo de Traza** (capturado automáticamente vía `monitor()`) es la fuente de verdad para todo el contexto de ejecución.
1. **Auditoría de Caja de Cristal**: El cumplimiento no es un booleano "pasa/falla"; es una historia verificable de ejecución.
1. **Prueba Inmutable**: El Hash de Evidencia te permite probar la integridad del proceso de auditoría.

______________________________________________________________________

**Siguiente Paso**: Tienes el Código (Nivel 1), las Operaciones (Nivel 2), y la Prueba (Nivel 3). Ahora genera los Documentos Legales. 👉 **[Ir al Nivel 4: El Arquitecto](https://venturalitica.github.io/venturalitica-sdk/es/academy/level4_annex_iv/index.md)**
