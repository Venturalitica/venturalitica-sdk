# Funcionalidades Experimentales

Esta pagina documenta los comandos CLI y funcionalidades que actualmente son experimentales. Su API puede cambiar o ser eliminada en futuras versiones.

!!! warning "Experimental"
    Estas funcionalidades dependen de la plataforma SaaS de Venturalitica, que aun no esta disponible publicamente. Se incluyen en el SDK para usuarios pioneros y pruebas internas.

---

## CLI: `login`

Autenticarse con la plataforma SaaS de Venturalitica.

```bash
venturalitica login
```

Almacena las credenciales localmente para su uso con los comandos `pull` y `push`. La autenticacion es necesaria antes de utilizar cualquier funcionalidad conectada al SaaS.

---

## CLI: `pull`

Descargar politicas OSCAL y configuracion del sistema desde la plataforma SaaS a tu proyecto local.

```bash
venturalitica pull
```

### Que Descarga

| Archivo | Descripcion |
| :--- | :--- |
| `model_policy.oscal.yaml` | Politica de equidad y rendimiento del modelo |
| `data_policy.oscal.yaml` | Politica de calidad y privacidad de datos |
| `system_description.yaml` | Campos de identidad del sistema segun Anexo IV.1 |

### Comportamiento

- Se autentica usando las credenciales almacenadas por `login`
- Obtiene las politicas desde `/api/pull?format=oscal`
- Escribe los archivos en el directorio de trabajo actual
- Reporta riesgos vinculados y no vinculados desde la plataforma SaaS

!!! note "Diferencia de Formato"
    El comando `pull` actualmente descarga politicas en formato OSCAL `system-security-plan`, mientras que el Editor de Politicas del Dashboard genera formato `assessment-plan`. Ambos formatos son soportados por el cargador del SDK, pero la diferencia puede causar confusion al editar politicas descargadas en el Dashboard. Esto se unificara en una futura version.

---

## CLI: `push`

Enviar evidencia de cumplimiento local a la plataforma SaaS de Venturalitica.

```bash
venturalitica push
```

Sube los resultados de aplicacion de politicas y archivos de trazabilidad desde `.venturalitica/` a la nube para visibilidad del equipo y pistas de auditoria.

---

## CLI: `ui` (Estable)

Lanzar el Dashboard Caja de Cristal local. Este comando es **estable** y esta completamente documentado.

```bash
venturalitica ui
```

Consulta la [Guia del Dashboard](dashboard.md) para la documentacion completa.

---

## Matriz de Estado de Funcionalidades

| Funcionalidad | Estado | Depende De |
| :--- | :--- | :--- |
| `venturalitica ui` | Estable | Solo local |
| `venturalitica login` | Experimental | Plataforma SaaS |
| `venturalitica pull` | Experimental | Plataforma SaaS |
| `venturalitica push` | Experimental | Plataforma SaaS |
| `vl.enforce()` | Estable | Solo local |
| `vl.monitor()` | Estable | Solo local |
| `vl.quickstart()` | Estable | Solo local |
| `vl.wrap()` | Experimental | Solo local |

---

## Enviar Comentarios

Si estas probando funcionalidades experimentales, reporta problemas en [GitHub Issues](https://github.com/venturalitica/venturalitica-sdk/issues/new).
