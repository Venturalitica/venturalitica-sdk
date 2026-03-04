# Dashboard Caja de Cristal

El **Dashboard de Venturalitica** es tu espacio de trabajo local para cumplimiento. Te guia a traves de 4 fases del ciclo de vida de cumplimiento de la Ley de IA de la UE sin salir de tu terminal.

## Lanzamiento

```bash
venturalitica ui
```

O con uv:

```bash
uv run venturalitica ui
```

El Dashboard se abre en `http://localhost:8501` en tu navegador predeterminado.

---

## Arquitectura del Dashboard

El Dashboard sigue un **recorrido de cumplimiento en 4 fases** mapeado a los requisitos de la Ley de IA de la UE:

```
Home (Centro de Control)
  |
  +-- Fase 1: Identidad del Sistema   (Anexo IV.1)
  |
  +-- Fase 2: Politica de Riesgos     (Articulos 9-10)
  |
  +-- Fase 3: Verificar y Evaluar     (Articulos 11-15)
  |       |
  |       +-- Feed de Transparencia
  |       +-- Integridad Tecnica
  |       +-- Aplicacion de Politicas
  |
  +-- Fase 4: Reporte Tecnico         (Anexo IV)
```

---

## Home: Centro de Control

La pantalla de inicio presenta 4 misiones como un panel de progreso. Cada mision muestra su estado de completitud:

| Mision | Verificacion de Estado | Descripcion |
| :--- | :--- | :--- |
| 1. Definir Sistema | Existe `system_description.yaml` | Identidad del sistema y descripcion de hardware |
| 2. Definir Politicas | Existe `model_policy.oscal.yaml` | Politicas OSCAL de riesgo y gobernanza de datos |
| 3. Verificar Evidencia | Existe `results.json` o `trace_*.json` | Telemetria, trazas y validacion de metricas |
| 4. Documentar | Existe `venturalitica_technical_doc.json` | Archivo tecnico del Anexo IV generado |

Haz clic en cualquier tarjeta de mision para navegar directamente a esa fase.

---

## Fase 1: Identidad del Sistema

**Ley de IA de la UE:** Anexo IV.1 (Descripcion General del Sistema de IA)

Define la "fuente de verdad" de tu sistema de IA usando el **Editor de Model Card**. Esto crea `system_description.yaml` con:

- **Nombre y version del sistema**
- **Proposito previsto** (ej., "Calificacion crediticia para solicitudes de prestamos")
- **Informacion del proveedor**
- **Descripcion de hardware** (recursos de computo utilizados)
- **Descripcion de interaccion** (como interactuan los usuarios con el sistema)

El editor proporciona un formulario estructurado. Todos los campos se mapean directamente a los requisitos del Anexo IV.1.

---

## Fase 2: Politica de Riesgos

**Ley de IA de la UE:** Articulos 9 (Gestion de Riesgos) y 10 (Gobernanza de Datos)

El **Editor de Politicas** permite crear y editar archivos de politicas OSCAL de forma visual. Genera YAML OSCAL en formato `assessment-plan` con:

- **Politica del Modelo** (`model_policy.oscal.yaml`): Controles de equidad y rendimiento para el comportamiento del modelo
- **Politica de Datos** (`data_policy.oscal.yaml`): Controles de calidad de datos y privacidad para los datos de entrenamiento

### Funcionalidades del Editor de Politicas

- Agregar controles con seleccion de metricas desde el registro completo
- Establecer umbrales y operadores de comparacion
- Mapear atributos protegidos (dimension binding)
- Previsualizar el YAML OSCAL generado
- Guardar directamente en el directorio de tu proyecto

!!! tip
    El Editor de Politicas genera formato `assessment-plan`, que es el formato OSCAL canonico utilizado en todo el SDK. Consulta la [Guia de Autoria de Politicas](policy-authoring.md) para el formato YAML manual.

---

## Fase 3: Verificar y Evaluar

**Ley de IA de la UE:** Articulos 11-15 (Documentacion Tecnica, Mantenimiento de Registros, Transparencia, Supervision Humana, Precision)

Esta fase requiere evidencia obtenida al ejecutar `vl.enforce()` y `vl.monitor()`. Selecciona una sesion de evidencia desde la barra lateral para inspeccionarla.

### Selector de Sesion

La barra lateral muestra todas las sesiones de evidencia disponibles:

- **Global / Historial**: Resultados agregados de `.venturalitica/results.json`
- **Sesiones con nombre**: Ejecuciones individuales de `vl.monitor("session_name")` con sus propios archivos de trazas

### Pestana: Feed de Transparencia

Se mapea al **Articulo 13** (Transparencia). Muestra:

- Lista de Materiales de Software (SBOM) -- todas las dependencias de Python con sus versiones
- Contexto de codigo -- analisis AST del script que genero la evidencia
- Metadatos de ejecucion -- marcas de tiempo, duracion, estado de exito/fallo

### Pestana: Integridad Tecnica

Se mapea al **Articulo 15** (Precision, Robustez, Ciberseguridad). Muestra:

- Huella digital del entorno (hash SHA-256)
- Deteccion de deriva de integridad (cambio el entorno durante la ejecucion?)
- Telemetria de hardware (pico de RAM, numero de CPUs)
- Emisiones de carbono (si CodeCarbon esta instalado)

### Pestana: Aplicacion de Politicas

Se mapea al **Articulo 9** (Gestion de Riesgos). Muestra:

- Resultados de cumplimiento por control con estado de aprobado/fallido
- Valores reales de metricas vs. umbrales de la politica
- Desglose visual de que controles pasaron y cuales fallaron
- Resumen de puntuacion de cumplimiento

---

## Fase 4: Reporte Tecnico

**Ley de IA de la UE:** Articulo 11 y Anexo IV (Documentacion Tecnica)

El **Generador de Anexo IV** produce la documentacion tecnica exhaustiva requerida para sistemas de IA de Alto Riesgo. Combina:

- **Datos de la Fase 1**: Identidad del sistema desde `system_description.yaml`
- **Datos de la Fase 2**: Politicas de riesgo desde los archivos OSCAL
- **Datos de la Fase 3**: Evidencia de los resultados de enforcement y trazas

### Seleccion de Proveedor LLM

| Proveedor | Privacidad | Soberania | Velocidad | Caso de Uso |
| :--- | :--- | :--- | :--- | :--- |
| Cloud (Mistral API) | Transporte cifrado | Alojado en la UE | Rapido | Acabado final |
| Local (Ollama) | 100% sin conexion | Generico | Mas lento | Pruebas iterativas |
| Soberano (ALIA) | Bloqueado por hardware | Nativo en espanol | Lento | Solo investigacion |

!!! warning "Requisitos de ALIA"
    ALIA es un modelo de 40B parametros que requiere ~41GB de RAM/VRAM. Es experimental.

### Proceso de Generacion

1. **Scanner**: Lee archivos de trazas y evidencia
2. **Planner**: Determina que secciones del Anexo IV aplican
3. **Writer**: Redacta cada seccion citando valores de metricas especificos
4. **Critic**: Revisa el borrador contra ISO 42001

### Salida

El generador produce:

- `venturalitica_technical_doc.json` -- datos estructurados
- `Annex_IV.md` -- documento markdown legible

Convertir a PDF:

```bash
# Simple
pip install mdpdf && mdpdf Annex_IV.md

# Avanzado
pandoc Annex_IV.md -o Annex_IV.pdf --toc --pdf-engine=xelatex
```

---

## Contexto de Proyecto

El Dashboard opera sobre tu **directorio de trabajo actual**. Lee los siguientes archivos:

| Archivo | Proposito |
| :--- | :--- |
| `system_description.yaml` | Identidad del sistema (Fase 1) |
| `model_policy.oscal.yaml` | Politica del modelo (Fase 2) |
| `data_policy.oscal.yaml` | Politica de datos (Fase 2) |
| `.venturalitica/results.json` | Resultados de enforcement (Fase 3) |
| `.venturalitica/trace_*.json` | Trazas de ejecucion (Fase 3) |
| `.venturalitica/bom.json` | Lista de materiales de software (Fase 3) |
| `venturalitica_technical_doc.json` | Documentacion generada (Fase 4) |

Ejecuta tus llamadas a `vl.enforce()` y `vl.monitor()` desde el mismo directorio donde lanzas `venturalitica ui`.

---

## Atajos de Teclado

El Dashboard utiliza Streamlit. Los atajos estandar de Streamlit aplican:

- `R` -- Volver a ejecutar la aplicacion
- `C` -- Limpiar cache
- Menu de configuracion (hamburguesa en la esquina superior derecha) para cambiar el tema
