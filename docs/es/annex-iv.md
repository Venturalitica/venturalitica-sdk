# Generando Documentación Técnica (Anexo IV)

Una de las partes más tediosas de la Ley de IA de la UE es el **Anexo IV**: el requisito de mantener documentación técnica actualizada.

Venturalítica automatiza esto tratando tus trazas de ejecución de código como la fuente de verdad.

## El Generador del Anexo IV

Puedes generar un borrador conforme de tu Documentación Técnica directamente desde el **Panel de Venturalítica**.

### Paso 1: Lanzar el Panel

Ejecuta la UI desde tu terminal en la raíz de tu proyecto:

```bash
venturalitica ui
```

### Paso 2: Navegar al "Generador de Anexo IV"

En la barra lateral izquierda, busca la sección **GENERAR REPORTES**.

1.  Haz clic en **📄 technical_doc.md**.
2.  El sistema analizará tu carpeta local `.venturalitica/`.
3.  Extraerá:
    *   **Arquitectura del Sistema** (de `bom.json`)
    *   **Estado de Gestión de Riesgos** (de los Resultados de Auditoría del Artículo 9)
    *   **Gobernanza de Datos** (de los Resultados de Auditoría del Artículo 10)
    *   **Ciberseguridad** (de los escaneos CVE)

### Paso 3: Descargar el Borrador

Verás una vista previa en vivo del archivo markdown generado.

*   Haz clic en **Descargar Borrador** para guardarlo como `Anexo_IV_Borrador.md`.
*   Luego puedes convertir este archivo Markdown a PDF usando tu herramienta preferida (ej., Pandoc o VS Code).

!!! tip "Actualizaciones Dinámicas"
    Cada vez que ejecutas `vl.enforce()`, la evidencia subyacente se actualiza. Generar un nuevo reporte siempre reflejará el último estado de tu sistema.

---

## Vía CLI (Alternativa)

Para canalizaciones de CI/CD, también puedes generar esta documentación sin abrir la UI:

```bash
venturalitica doc --output docs/technical_file.md
```

Este comando realiza la misma lógica pero guarda el archivo directamente en tu ruta especificada.
