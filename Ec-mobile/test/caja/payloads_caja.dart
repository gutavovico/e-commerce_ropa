/// Payloads literales de la caja, generados con los esquemas Pydantic del backend
/// (`cu31_cu32_punto_venta/esquemas.py` y `MiSucursalOut`, con `model_dump_json`). No se arman sobre
/// los DTO de la app: así las pruebas ejercitan `fromJson` de verdad (lección de CU12 móvil).
const String variante =
    '{"id_variante":41,"sku":"MSH-CAM-M","id_producto":5,"nombre_producto":"Camisa formal blanca","categoria_nombre":"Camisas formales","talla_codigo":"M","color_nombre":"Blanco","imagen_url":"/ar/menshopping_camisa.png","precio_lista":"350.00","precio_final":"350.00","disponible_en_sucursal":5}';

const String varianteAgotada =
    '{"id_variante":42,"sku":"MSH-CAM-L","id_producto":5,"nombre_producto":"Camisa formal blanca","categoria_nombre":"Camisas formales","talla_codigo":"L","color_nombre":"Blanco","imagen_url":null,"precio_lista":"350.00","precio_final":"350.00","disponible_en_sucursal":0}';

const String _linea =
    '{"id_variante":41,"sku":"MSH-CAM-M","nombre_producto":"Camisa formal blanca","talla_codigo":"M","color_nombre":"Blanco","imagen_url":null,"cantidad":1,"precio_lista":"350.00","precio_unitario":"350.00","subtotal_linea":"350.00","motivo_descuento":null,"origen":"caja"}';

const String previsualizacion =
    '{"subtotal":"350.00","descuento":"0.00","total":"350.00","iva_incluido":"40.27","cupon_aplicado":null,"lineas":[$_linea],"lineas_reserva_excluidas":[]}';

const String cliente = '{"id_cliente":10,"nombres":"Ana","apellidos":"Rojas","email":"ana@ejemplo.com"}';

const String reserva =
    '{"id_reserva":123,"codigo":"RES-2026-0123","estado":"confirmada","fecha_hora_atencion":"2026-11-10T15:00:00Z","cliente":$cliente,"lineas":[{"id_variante":41,"sku":"MSH-CAM-M","nombre_producto":"Camisa formal blanca","talla_codigo":"M","color_nombre":"Blanco","cantidad":1}]}';

const String cupon =
    '{"codigo":"OTONO10","nombre":"Otoño","descripcion":null,"tipo_descuento":"porcentaje","valor_descuento":"10.00","alcance":"global","fecha_fin":"2026-11-10T15:00:00Z","usos_restantes":5}';

const String _cabeceraVenta =
    '"subtotal":"350.00","descuento":"0.00","total":"350.00","iva_incluido":"40.27","cupon_aplicado":null,"id_venta":501,"numero_comprobante":"MOV-2026-00501","fecha_venta":"2026-11-10T15:00:00Z","id_sucursal":3,"nombre_sucursal":"Menshopping Santa Cruz","direccion_sucursal":"Dirección por confirmar","cajero_nombre":"Carlos Perez","cliente":null,"reserva_codigo":null,"lineas":[$_linea],"lineas_reserva_excluidas":[]';

const String ventaPendiente = '{$_cabeceraVenta,"estado":"pendiente","pagos":[]}';

const String ventaPagada =
    '{$_cabeceraVenta,"estado":"pagada","pagos":[{"id_pago":90,"metodo_pago":"efectivo","monto":"350.00","estado":"confirmado","referencia":null,"monto_recibido":"400.00","cambio":"50.00","creado_en":"2026-11-10T15:00:00Z","confirmado_en":"2026-11-10T15:00:00Z"}]}';

const String pedidoWeb =
    '{"id_pago":77,"id_venta":480,"numero_comprobante":"WEB-2026-00480","cliente_nombre":"Ana Rojas","total":"280.00","creado_en":"2026-11-10T15:00:00Z"}';

const String sucursal =
    '{"id_sucursal":3,"nombre":"Menshopping Santa Cruz","ciudad":"Santa Cruz de la Sierra","es_principal":true}';

const String sucursal2 =
    '{"id_sucursal":4,"nombre":"Menshopping Beni","ciudad":"Trinidad","es_principal":false}';
