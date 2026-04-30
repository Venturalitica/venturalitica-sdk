# Nivel 3: El Auditor (Traza de Caja de Cristal)

**Objetivo**: Verificar tu politica visual y criptograficamente usando el metodo de **Caja de Cristal**.

**Prerrequisito**: [Nivel 2 (El Integrador)](level2_integrator.md)

---

## 1. El Problema: "Paso, pero podemos confiar en el proceso?"

En el Nivel 2, registraste el puntaje de cumplimiento. Pero para la **IA de Alto Riesgo** (como el Scoring de Credito), las metricas no son suficientes.
Un Auditor pregunta: *"Probaste en el dataset real, o filtraste los prestamos rechazados?"* y *"Puedes probar que este codigo fue realmente ejecutado?"*

## 2. La Solucion: La Traza de "Caja de Cristal"

Segun nuestros **Documentos de Auditoria Estrategica**, la auditoria profesional requiere mas que resultados--requiere **Proveniencia**.

Venturalitica usa un context manager `monitor()` para registrar todo:

-   **El Codigo**: Analisis AST de tu script.
-   **Los Datos**: Conteo de filas y esquema de columnas.
-   **El Hardware**: Memoria, CPU y estadisticas de Carbono (Articulo 15).
-   **El Sello**: Un hash criptografico SHA-256 de toda la sesion.

### El Upgrade

Continuamos trabajando en el mismo proyecto. No se requiere configuracion nueva.

### Ejecutar con el Monitor Nativo

Envuelve tu ejecucion en `vl.monitor()`. Este context manager captura el "Handshake" entre tu codigo y la politica cosechando metadatos fisicos y logicos.

### Profundizacion: Caja de Cristal vs Caja Negra

| Caracteristica | Caja Negra (Estandar) | **Caja de Cristal (Venturalitica)** |
| :--- | :--- | :--- |
| **Logica** | "Confia en mi, ejecute el codigo." | **Analisis AST**: Registramos *que* funcion mapeo codigo a politica. |
| **Datos** | "Aqui esta el CSV." | **Huella Digital**: Registramos el SHA-256 del dataset en tiempo de ejecucion. |
| **Alcance** | Codigo | Codigo + Entorno + Estadisticas de Hardware |

> Codigo completo: Consulta el ciclo de vida profesional de auditoria en el notebook [01_assurance_audit.ipynb](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/01_assurance_audit.ipynb).

```python
import venturalitica as vl
from venturalitica.quickstart import load_sample

# 1. Iniciar el Monitor Multimodal (La Caja de Cristal)
with vl.monitor("loan_audit_v1"):
    # Este bloque ahora esta siendo vigilado por el Auditor
    df = load_sample("loan")
    
    # Descarga data_policy.oscal.yaml desde:
    # https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/data_policy.oscal.yaml
    results = vl.enforce(
        data=df,
        target="class",
        gender="Attribute9",  # Mapeando genero
        age="Attribute13",    # Mapeando edad
        policy="data_policy.oscal.yaml"
    )
    # El archivo de traza de sesion (.venturalitica/trace_loan_audit_v1.json) 
    # probara NO solo el resultado, sino COMO fue computado.

# Despues de que el context manager termine, revisa el directorio de evidencia:
# .venturalitica/
#   trace_loan_audit_v1.json   <- Traza completa de ejecucion
#   results.json               <- Resultados de cumplimiento
```


## 3. La Verificacion del "Sello Digital"

Despues de ejecutar la auditoria, lanza la UI:

```bash
pip install venturalitica[dashboard]   # Requerido para la interfaz
venturalitica ui
```

Navega a **"Articulo 13: Transparencia"**.

### Encontrando el Hash de Evidencia
Busca el **Evidence Hash** en el Dashboard.
`Evidence Hash: 89fbf...`

Este hash es tu **"Sello Digital"**. Si cambias *un pixel* en el dataset o *una linea* en la politica, este hash cambia. Ahora puedes probar a un regulador exactamente que paso durante la auditoria.

## 4. El Mapa de Cumplimiento

El Dashboard traduce la evidencia JSON al lenguaje de la **EU AI Act**.

| Ley | Pestana del Dashboard | Que Responder |
| :--- | :--- | :--- |
| **Art 9** | Gestion de Riesgos | "Verificamos sesgo < 0.1?" (Tu Politica) |
| **Art 10** | Assurance de Datos | "Son los datos de entrenamiento representativos?" |
| **Art 13** | Transparencia | "Que librerias (BOM) estamos usando?" |

## 5. Mensajes para Llevar a Casa

1.  **No Confies, Verifica**: El **Archivo de Traza** (capturado automaticamente via `monitor()`) es la fuente de verdad para todo el contexto de ejecucion.
2.  **Auditoria de Caja de Cristal**: El cumplimiento no es un booleano "pasa/falla"; es una historia verificable de ejecucion.
3.  **Prueba Inmutable**: El Evidence Hash te permite probar la integridad del proceso de auditoria.

---

---

### Referencias

- **[Referencia de Probes](../probes.md)** -- Detalles sobre los 7 probes de evidencia
- **[Guia del Dashboard](../dashboard.md)** -- Recorrido completo de las fases del Dashboard
- **[Ciclo de Vida Completo](../full-lifecycle.md)** -- Guia de extremo a extremo en una sola pagina

**[Ir al Nivel 4: El Arquitecto](level4_annex_iv.md)**
