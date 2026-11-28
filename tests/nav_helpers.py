"""Ayuda de navegación de pruebas: seleccionar primero destino, luego pestaña."""

DESTINO_POR_HREF = {
    "#cotizador": "pedido", "#costos": "pedido", "#ruta": "pedido",
    "#operar": "operacion", "#cierre": "operacion",
    "#portada": "costos", "#dashboard": "costos", "#periodos": "costos",
    "#reportes": "costos", "#inventarios": "costos", "#normal": "costos",
    "#proyeccion": "futuro", "#laboratorio": "futuro", "#familias": "futuro",
    "#comparar": "futuro", "#decidir": "futuro", "#propuestas": "futuro",
    "#aprendido": "aprendizaje", "#analisis": "aprendizaje",
    "#modelo": "configuracion", "#datos": "configuracion", "#cargar-libro": "configuracion",
    "#espacios": "configuracion", "#consultar": "configuracion", "#control": "configuracion",
}


def ir_a_pestana(page, href):
    """Abre el grupo que contiene href y navega con su pestaña superior."""
    destino = DESTINO_POR_HREF[href]
    grupo = page.locator(f'#nav-destinos details[data-destino="{destino}"]')
    if not grupo.evaluate("e => e.open"):
        grupo.locator("summary").click()
    page.locator(f'#module-tabs [role="tab"][href="{href}"]').click()
