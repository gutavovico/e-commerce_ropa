/// Payloads literales de P2-CU18, generados con los esquemas Pydantic de `cu18_cambio_prenda`
/// (`model_dump_json`).
const String venta =
    '{"id_venta":501,"numero_comprobante":"FS-2026-000501","fecha_venta":"2026-11-10T15:00:00Z","cliente_nombre":"Ana Rojas","total":"450.00","dias_transcurridos":5,"plazo_dias":15,"lineas":[{"id_venta_detalle":1,"id_variante":41,"sku":"MSH-CAM-M","nombre_producto":"Camisa formal blanca","talla_codigo":"M","color_nombre":"Blanco","vendidas":2,"ya_cambiadas":0,"cambiables":2,"valor_unitario":"90.00"}]}';

const String _lineas =
    '"devueltas":[{"tipo":"devuelta","id_venta_detalle":1,"id_variante":41,"sku":"MSH-CAM-M","nombre_producto":"Camisa formal blanca","talla_codigo":"M","color_nombre":"Blanco","cantidad":1,"precio_unitario":"90.00","subtotal":"90.00","motivo_descuento":null}],"nuevas":[{"tipo":"nueva","id_venta_detalle":null,"id_variante":42,"sku":"MSH-CAM-L","nombre_producto":"Camisa formal blanca","talla_codigo":"L","color_nombre":"Blanco","cantidad":1,"precio_unitario":"100.00","subtotal":"100.00","motivo_descuento":null}]';

const String previo = '{$_lineas,"valor_devuelto":"90.00","valor_nuevo":"100.00","diferencia":"10.00"}';

const String cambio =
    '{$_lineas,"valor_devuelto":"90.00","valor_nuevo":"100.00","diferencia":"10.00","id_cambio":7,"numero_comprobante":"CAM-2026-00001","creado_en":"2026-11-10T15:00:00Z","id_venta":501,"comprobante_venta":"FS-2026-000501","id_sucursal":3,"nombre_sucursal":"Menshopping Santa Cruz","atendido_por":"Carlos Perez","metodo_pago":"efectivo","monto_recibido":"20.00","vuelto":"10.00","referencia":null,"devuelto_al_cliente":"0.00"}';
