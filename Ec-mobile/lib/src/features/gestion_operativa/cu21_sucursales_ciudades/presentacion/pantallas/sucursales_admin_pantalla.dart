import 'package:flutter/material.dart';
import 'package:ec_mobile/src/core/theme/app_theme.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/sucursal.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_bloc.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_estado.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/widgets/formulario_sucursal_sheet.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/widgets/selector_ciudades_chips.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/widgets/shimmer_carga_sucursales.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/widgets/tarjeta_sucursal.dart';

/// Pantalla principal de gestion administrativa de boutiques y territorios (AC-15, AC-16, AC-17, AC-18).
class SucursalesAdminPantalla extends StatefulWidget {
  final String token;
  final SucursalesBloc? bloc;

  const SucursalesAdminPantalla({
    super.key,
    required this.token,
    this.bloc,
  });

  @override
  State<SucursalesAdminPantalla> createState() =>
      _SucursalesAdminPantallaState();
}

class _SucursalesAdminPantallaState extends State<SucursalesAdminPantalla> {
  late final SucursalesBloc _bloc;
  final TextEditingController _busquedaCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? SucursalesBloc();
    _bloc.addListener(_alCambiarEstado);
    _bloc.cargarDatos(widget.token);
  }

  @override
  void dispose() {
    _bloc.removeListener(_alCambiarEstado);
    if (widget.bloc == null) {
      _bloc.dispose();
    }
    _busquedaCtrl.dispose();
    super.dispose();
  }

  void _alCambiarEstado() {
    if (!mounted) return;
    setState(() {});

    final estado = _bloc.estado;
    if (estado is SucursalesCargado) {
      if (estado.mensajeExito != null && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              estado.mensajeExito!,
              style: AppTypography.caption.copyWith(color: AppColors.white),
            ),
            backgroundColor: AppColors.primary900,
            duration: const Duration(seconds: 3),
            behavior: SnackBarBehavior.floating,
            shape: const RoundedRectangleBorder(
              borderRadius: AppRadius.radiusSmall,
            ),
          ),
        );
        _bloc.limpiarAlertas();
      } else if (estado.mensajeError != null && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              estado.mensajeError!,
              style: AppTypography.caption.copyWith(color: AppColors.white),
            ),
            backgroundColor: AppColors.rose700,
            duration: const Duration(seconds: 4),
            behavior: SnackBarBehavior.floating,
            shape: const RoundedRectangleBorder(
              borderRadius: AppRadius.radiusSmall,
            ),
          ),
        );
        _bloc.limpiarAlertas();
      }
    }
  }

  void _abrirFormularioBoutique({Sucursal? sucursalParaEditar}) {
    final estado = _bloc.estado;
    if (estado is! SucursalesCargado) return;

    showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) {
        return FormularioSucursalSheet(
          ciudades: estado.ciudades,
          sucursalParaEditar: sucursalParaEditar,
          alGuardar: ({
            required idCiudad,
            required nombre,
            required direccion,
            telefono,
            required horarioApertura,
            required horarioCierre,
          }) {
            if (sucursalParaEditar != null) {
              return _bloc.actualizarSucursal(
                widget.token,
                sucursalParaEditar.idSucursal,
                idCiudad: idCiudad,
                nombre: nombre,
                direccion: direccion,
                telefono: telefono,
                horarioApertura: horarioApertura,
                horarioCierre: horarioCierre,
              );
            } else {
              return _bloc.crearSucursal(
                widget.token,
                idCiudad: idCiudad,
                nombre: nombre,
                direccion: direccion,
                telefono: telefono,
                horarioApertura: horarioApertura,
                horarioCierre: horarioCierre,
              );
            }
          },
        );
      },
    );
  }

  void _confirmarEliminarSucursal(Sucursal sucursal) {
    showDialog<bool>(
      context: context,
      builder: (dialogCtx) {
        return AlertDialog(
          backgroundColor: AppColors.white,
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.radiusLarge,
          ),
          title: Text(
            'Confirmar Eliminacion',
            style: AppTypography.h3,
          ),
          content: Text(
            'Esta seguro de eliminar la boutique "${sucursal.nombre}"? '
            'Esta accion no podra completarse si cuenta con reservas o stock asociado.',
            style: AppTypography.body,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogCtx).pop(false),
              child: Text(
                'CANCELAR',
                style: AppTypography.labelSmall.copyWith(
                  color: AppColors.slate500,
                ),
              ),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.rose600,
                foregroundColor: AppColors.white,
                shape: const RoundedRectangleBorder(
                  borderRadius: AppRadius.radiusSmall,
                ),
              ),
              onPressed: () => Navigator.of(dialogCtx).pop(true),
              child: Text(
                'ELIMINAR',
                style: AppTypography.labelSmall.copyWith(
                  color: AppColors.white,
                ),
              ),
            ),
          ],
        );
      },
    ).then((confirmado) {
      if (confirmado == true) {
        _bloc.eliminarSucursal(widget.token, sucursal.idSucursal);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final estado = _bloc.estado;

    return Scaffold(
      backgroundColor: AppColors.slate50,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'FASHION STORE',
              style: AppTypography.labelSmall.copyWith(
                color: AppColors.secondary500,
                letterSpacing: 1.5,
              ),
            ),
            Text(
              'Gestion Territorial',
              style: AppTypography.h3,
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, size: 20),
            onPressed: () => _bloc.cargarDatos(widget.token),
            tooltip: 'Recargar datos',
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.primary900,
        foregroundColor: AppColors.white,
        elevation: 2,
        onPressed: () => _abrirFormularioBoutique(),
        icon: const Icon(Icons.add, size: 18, color: AppColors.secondary500),
        label: Text(
          'NUEVA BOUTIQUE',
          style: AppTypography.button.copyWith(fontSize: 11),
        ),
      ),
      body: switch (estado) {
        SucursalesInicial() => const SizedBox.shrink(),
        SucursalesCargando() => const ShimmerCargaSucursales(),
        SucursalesError(:final mensaje) => _construirVistaError(mensaje),
        SucursalesCargado() => _construirVistaPrincipal(estado),
      },
    );
  }

  Widget _construirVistaError(String mensaje) {
    return Center(
      child: Padding(
        padding: AppSpacing.paddingDialog,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: AppSpacing.paddingSpace4,
              decoration: const BoxDecoration(
                color: AppColors.rose50,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.error_outline,
                size: 40,
                color: AppColors.rose600,
              ),
            ),
            AppSpacing.gapVSpace4,
            Text(
              'Fallo de Sincronizacion',
              style: AppTypography.h2,
            ),
            AppSpacing.gapVSpace2,
            Text(
              mensaje,
              style: AppTypography.body,
              textAlign: TextAlign.center,
            ),
            AppSpacing.gapVSpace5,
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary900,
                foregroundColor: AppColors.white,
                padding: AppSpacing.paddingHorizontalSpace5,
                shape: const RoundedRectangleBorder(
                  borderRadius: AppRadius.radiusMedium,
                ),
              ),
              onPressed: () => _bloc.cargarDatos(widget.token),
              child: Text('REINTENTAR', style: AppTypography.button),
            ),
          ],
        ),
      ),
    );
  }

  Widget _construirVistaPrincipal(SucursalesCargado estado) {
    final sucursalesFiltradas = estado.sucursalesFiltradas;

    return RefreshIndicator(
      onRefresh: () => _bloc.cargarDatos(widget.token),
      color: AppColors.primary900,
      child: Column(
        children: [
          // 1. Barra de Busqueda Textual
          Padding(
            padding: const EdgeInsets.only(
              left: AppSpacing.space4,
              right: AppSpacing.space4,
              top: AppSpacing.space3,
            ),
            child: TextField(
              controller: _busquedaCtrl,
              style: AppTypography.body,
              decoration: InputDecoration(
                hintText: 'Buscar por nombre, direccion o ciudad...',
                hintStyle: AppTypography.caption,
                prefixIcon: const Icon(
                  Icons.search,
                  size: 18,
                  color: AppColors.slate400,
                ),
                suffixIcon: _busquedaCtrl.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 16),
                        onPressed: () {
                          _busquedaCtrl.clear();
                          _bloc.actualizarBusqueda('');
                        },
                      )
                    : null,
                filled: true,
                fillColor: AppColors.white,
                contentPadding: AppSpacing.paddingSpace3,
                border: OutlineInputBorder(
                  borderRadius: AppRadius.radiusLarge,
                  borderSide: const BorderSide(color: AppColors.slate200),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: AppRadius.radiusLarge,
                  borderSide: const BorderSide(color: AppColors.slate200),
                ),
              ),
              onChanged: (val) => _bloc.actualizarBusqueda(val),
            ),
          ),

          AppSpacing.gapVSpace3,

          // 2. Selector Horizontal de Ciudades en Chips (AC-17)
          SelectorCiudadesChips(
            ciudades: estado.ciudades,
            ciudadSeleccionadaId: estado.ciudadFiltroId,
            alSeleccionarCiudad: (id) => _bloc.seleccionarFiltroCiudad(id),
          ),

          AppSpacing.gapVSpace3,

          // 3. Barra de Metricas y Filtros de Estado
          Padding(
            padding: AppSpacing.paddingHorizontalSpace4,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Contador Resumen
                Row(
                  children: [
                    Text(
                      '${sucursalesFiltradas.length}',
                      style: AppTypography.h3.copyWith(
                        color: AppColors.primary900,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    AppSpacing.gapHSpace1,
                    Text(
                      sucursalesFiltradas.length == 1
                          ? 'boutique'
                          : 'boutiques',
                      style: AppTypography.caption,
                    ),
                  ],
                ),

                // Filtro Estado (Todos / Activas / Inactivas)
                Row(
                  children: [
                    _construirBotonFiltroEstado(
                      etiqueta: 'TODAS',
                      activo: estado.estadoFiltro == null,
                      alPulsar: () => _bloc.actualizarFiltroEstado(null),
                    ),
                    AppSpacing.gapHSpace1,
                    _construirBotonFiltroEstado(
                      etiqueta: 'ACTIVAS',
                      activo: estado.estadoFiltro == true,
                      alPulsar: () => _bloc.actualizarFiltroEstado(true),
                    ),
                    AppSpacing.gapHSpace1,
                    _construirBotonFiltroEstado(
                      etiqueta: 'INACTIVAS',
                      activo: estado.estadoFiltro == false,
                      alPulsar: () => _bloc.actualizarFiltroEstado(false),
                    ),
                  ],
                ),
              ],
            ),
          ),

          AppSpacing.gapVSpace3,

          // 4. Listado Vertical de Tarjetas de Boutiques
          Expanded(
            child: sucursalesFiltradas.isNotEmpty
                ? ListView.separated(
                    padding: const EdgeInsets.only(
                      left: AppSpacing.space4,
                      right: AppSpacing.space4,
                      bottom: AppSpacing.space7 + AppSpacing.space4,
                    ),
                    itemCount: sucursalesFiltradas.length,
                    separatorBuilder: (context, index) => AppSpacing.gapVSpace3,
                    itemBuilder: (context, index) {
                      final sucursal = sucursalesFiltradas[index];
                      return TarjetaSucursal(
                        key: ValueKey('tarjeta_${sucursal.idSucursal}'),
                        sucursal: sucursal,
                        alAlternarEstado: (nuevoEstado) {
                          _bloc.cambiarEstadoSucursal(
                            widget.token,
                            sucursal.idSucursal,
                            nuevoEstado,
                          );
                        },
                        alEditar: () {
                          _abrirFormularioBoutique(
                            sucursalParaEditar: sucursal,
                          );
                        },
                        alEliminar: () {
                          _confirmarEliminarSucursal(sucursal);
                        },
                      );
                    },
                  )
                : _construirEstadoVacio(),
          ),
        ],
      ),
    );
  }

  Widget _construirBotonFiltroEstado({
    required String etiqueta,
    required bool activo,
    required VoidCallback alPulsar,
  }) {
    return InkWell(
      onTap: alPulsar,
      borderRadius: AppRadius.radiusSmall,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space2,
          vertical: AppSpacing.space1,
        ),
        decoration: BoxDecoration(
          color: activo ? AppColors.primary900 : Colors.transparent,
          borderRadius: AppRadius.radiusSmall,
        ),
        child: Text(
          etiqueta,
          style: AppTypography.labelSmall.copyWith(
            fontSize: 9,
            color: activo ? AppColors.white : AppColors.slate500,
            fontWeight: activo ? FontWeight.w700 : FontWeight.w500,
          ),
        ),
      ),
    );
  }

  Widget _construirEstadoVacio() {
    return Center(
      child: Padding(
        padding: AppSpacing.paddingDialog,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.storefront_outlined,
              size: 48,
              color: AppColors.slate300,
            ),
            AppSpacing.gapVSpace3,
            Text(
              'No se encontraron boutiques',
              style: AppTypography.h3.copyWith(
                color: AppColors.slate700,
              ),
            ),
            AppSpacing.gapVSpace1,
            Text(
              'Intente ajustar los filtros de busqueda o registre una nueva boutique.',
              style: AppTypography.caption,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
