import 'package:flutter/material.dart';
import 'package:ec_mobile/src/core/theme/app_theme.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/ciudad.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/sucursal.dart';

/// Modal BottomSheet para alta y edicion de boutiques (AC-18).
class FormularioSucursalSheet extends StatefulWidget {
  final List<Ciudad> ciudades;
  final Sucursal? sucursalParaEditar;
  final Future<bool> Function({
    required int idCiudad,
    required String nombre,
    required String direccion,
    String? telefono,
    required String horarioApertura,
    required String horarioCierre,
  }) alGuardar;

  const FormularioSucursalSheet({
    super.key,
    required this.ciudades,
    this.sucursalParaEditar,
    required this.alGuardar,
  });

  @override
  State<FormularioSucursalSheet> createState() =>
      _FormularioSucursalSheetState();
}

class _FormularioSucursalSheetState extends State<FormularioSucursalSheet> {
  final _formKey = GlobalKey<FormState>();

  late int _idCiudadSeleccionada;
  late final TextEditingController _nombreCtrl;
  late final TextEditingController _direccionCtrl;
  late final TextEditingController _telefonoCtrl;
  late final TextEditingController _aperturaCtrl;
  late final TextEditingController _cierreCtrl;

  bool _enviando = false;
  String? _errorCoherenciaHoraria;

  @override
  void initState() {
    super.initState();
    final editando = widget.sucursalParaEditar;

    _idCiudadSeleccionada = editando?.idCiudad ??
        (widget.ciudades.isNotEmpty ? widget.ciudades.first.idCiudad : 0);

    _nombreCtrl = TextEditingController(text: editando?.nombre ?? '');
    _direccionCtrl = TextEditingController(text: editando?.direccion ?? '');
    _telefonoCtrl = TextEditingController(text: editando?.telefono ?? '');
    _aperturaCtrl =
        TextEditingController(text: editando?.horarioApertura ?? '10:00');
    _cierreCtrl =
        TextEditingController(text: editando?.horarioCierre ?? '20:30');
  }

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _direccionCtrl.dispose();
    _telefonoCtrl.dispose();
    _aperturaCtrl.dispose();
    _cierreCtrl.dispose();
    super.dispose();
  }

  bool _validarHorarios(String apertura, String cierre) {
    final regex = RegExp(r'^([01]\d|2[0-3]):[0-5]\d$');
    if (!regex.hasMatch(apertura) || !regex.hasMatch(cierre)) {
      setState(() {
        _errorCoherenciaHoraria =
            'Formato de hora no valido. Utilice el patron HH:mm (ej. 10:00).';
      });
      return false;
    }

    if (cierre.compareTo(apertura) <= 0) {
      setState(() {
        _errorCoherenciaHoraria =
            'El horario de cierre debe ser posterior a la hora de apertura.';
      });
      return false;
    }

    setState(() {
      _errorCoherenciaHoraria = null;
    });
    return true;
  }

  Future<void> _enviarFormulario() async {
    if (_enviando) return;

    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    final apertura = _aperturaCtrl.text.trim();
    final cierre = _cierreCtrl.text.trim();

    if (!_validarHorarios(apertura, cierre)) {
      return;
    }

    setState(() => _enviando = true);

    final exito = await widget.alGuardar(
      idCiudad: _idCiudadSeleccionada,
      nombre: _nombreCtrl.text.trim(),
      direccion: _direccionCtrl.text.trim(),
      telefono: _telefonoCtrl.text.trim().isNotEmpty
          ? _telefonoCtrl.text.trim()
          : null,
      horarioApertura: apertura,
      horarioCierre: cierre,
    );

    if (mounted) {
      setState(() => _enviando = false);
      if (exito) {
        Navigator.of(context).pop(true);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final esEdicion = widget.sucursalParaEditar != null;

    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Container(
        decoration: const BoxDecoration(
          color: AppColors.white,
          borderRadius: AppRadius.radiusSheet,
        ),
        padding: AppSpacing.paddingSheet,
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Tirador superior del BottomSheet
                Center(
                  child: Container(
                    width: AppSpacing.space6,
                    height: AppSpacing.space2,
                    decoration: BoxDecoration(
                      color: AppColors.slate300,
                      borderRadius: AppRadius.radiusSmall,
                    ),
                  ),
                ),
                AppSpacing.gapVSpace3,

                // Titulo del Drawer
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      esEdicion
                          ? 'EDITAR BOUTIQUE'
                          : 'NUEVA BOUTIQUE',
                      style: AppTypography.h3.copyWith(
                        letterSpacing: 0.5,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 20),
                      onPressed: () => Navigator.of(context).pop(false),
                    ),
                  ],
                ),
                AppSpacing.gapVSpace3,

                // 1. Selector de Ciudad
                Text(
                  'CIUDAD TERRITORIAL *',
                  style: AppTypography.labelSmall,
                ),
                AppSpacing.gapVSpace1,
                DropdownButtonFormField<int>(
                  initialValue: _idCiudadSeleccionada,
                  decoration: InputDecoration(
                    contentPadding: AppSpacing.paddingSpace3,
                    border: OutlineInputBorder(
                      borderRadius: AppRadius.radiusMedium,
                      borderSide: const BorderSide(color: AppColors.slate200),
                    ),
                    filled: true,
                    fillColor: AppColors.slate50,
                  ),
                  items: widget.ciudades.map((c) {
                    return DropdownMenuItem<int>(
                      value: c.idCiudad,
                      child: Text(
                        '${c.nombre} (${c.pais})',
                        style: AppTypography.body,
                      ),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() => _idCiudadSeleccionada = val);
                    }
                  },
                ),
                AppSpacing.gapVSpace3,

                // 2. Nombre
                Text(
                  'NOMBRE DEL ESTABLECIMIENTO *',
                  style: AppTypography.labelSmall,
                ),
                AppSpacing.gapVSpace1,
                TextFormField(
                  controller: _nombreCtrl,
                  style: AppTypography.body,
                  decoration: InputDecoration(
                    hintText: 'Ej. Atelier Serrano Haute Couture',
                    hintStyle: AppTypography.caption,
                    contentPadding: AppSpacing.paddingSpace3,
                    border: OutlineInputBorder(
                      borderRadius: AppRadius.radiusMedium,
                      borderSide: const BorderSide(color: AppColors.slate200),
                    ),
                    filled: true,
                    fillColor: AppColors.slate50,
                  ),
                  validator: (v) {
                    if (v == null || v.trim().length < 3) {
                      return 'El nombre debe tener al menos 3 caracteres.';
                    }
                    return null;
                  },
                ),
                AppSpacing.gapVSpace3,

                // 3. Direccion
                Text(
                  'DIRECCION FISICA *',
                  style: AppTypography.labelSmall,
                ),
                AppSpacing.gapVSpace1,
                TextFormField(
                  controller: _direccionCtrl,
                  style: AppTypography.body,
                  decoration: InputDecoration(
                    hintText: 'Ej. Calle de Serrano 45',
                    hintStyle: AppTypography.caption,
                    contentPadding: AppSpacing.paddingSpace3,
                    border: OutlineInputBorder(
                      borderRadius: AppRadius.radiusMedium,
                      borderSide: const BorderSide(color: AppColors.slate200),
                    ),
                    filled: true,
                    fillColor: AppColors.slate50,
                  ),
                  validator: (v) {
                    if (v == null || v.trim().length < 5) {
                      return 'La direccion debe tener al menos 5 caracteres.';
                    }
                    return null;
                  },
                ),
                AppSpacing.gapVSpace3,

                // 4. Telefono
                Text(
                  'TELEFONO DE CONTACTO',
                  style: AppTypography.labelSmall,
                ),
                AppSpacing.gapVSpace1,
                TextFormField(
                  controller: _telefonoCtrl,
                  style: AppTypography.body,
                  keyboardType: TextInputType.phone,
                  decoration: InputDecoration(
                    hintText: '+34 910 123 456',
                    hintStyle: AppTypography.caption,
                    contentPadding: AppSpacing.paddingSpace3,
                    border: OutlineInputBorder(
                      borderRadius: AppRadius.radiusMedium,
                      borderSide: const BorderSide(color: AppColors.slate200),
                    ),
                    filled: true,
                    fillColor: AppColors.slate50,
                  ),
                ),
                AppSpacing.gapVSpace3,

                // 5. Horarios de Apertura y Cierre
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('APERTURA (HH:mm) *',
                              style: AppTypography.labelSmall),
                          AppSpacing.gapVSpace1,
                          TextFormField(
                            controller: _aperturaCtrl,
                            style: AppTypography.body,
                            decoration: InputDecoration(
                              hintText: '10:00',
                              hintStyle: AppTypography.caption,
                              contentPadding: AppSpacing.paddingSpace3,
                              border: OutlineInputBorder(
                                borderRadius: AppRadius.radiusMedium,
                                borderSide:
                                    const BorderSide(color: AppColors.slate200),
                              ),
                              filled: true,
                              fillColor: AppColors.slate50,
                            ),
                          ),
                        ],
                      ),
                    ),
                    AppSpacing.gapHSpace3,
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('CIERRE (HH:mm) *',
                              style: AppTypography.labelSmall),
                          AppSpacing.gapVSpace1,
                          TextFormField(
                            controller: _cierreCtrl,
                            style: AppTypography.body,
                            decoration: InputDecoration(
                              hintText: '20:30',
                              hintStyle: AppTypography.caption,
                              contentPadding: AppSpacing.paddingSpace3,
                              border: OutlineInputBorder(
                                borderRadius: AppRadius.radiusMedium,
                                borderSide:
                                    const BorderSide(color: AppColors.slate200),
                              ),
                              filled: true,
                              fillColor: AppColors.slate50,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),

                // Error de Coherencia Horaria
                if (_errorCoherenciaHoraria != null) ...[
                  AppSpacing.gapVSpace2,
                  Container(
                    padding: AppSpacing.paddingSpace3,
                    decoration: BoxDecoration(
                      color: AppColors.rose50,
                      borderRadius: AppRadius.radiusSmall,
                      border: Border.all(color: AppColors.rose200),
                    ),
                    child: Text(
                      _errorCoherenciaHoraria!,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.rose700,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],

                AppSpacing.gapVSpace5,

                // Boton de Envio
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary900,
                    foregroundColor: AppColors.white,
                    padding: AppSpacing.paddingSpace4,
                    shape: const RoundedRectangleBorder(
                      borderRadius: AppRadius.radiusMedium,
                    ),
                  ),
                  onPressed: _enviando ? null : _enviarFormulario,
                  child: _enviando
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            color: AppColors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : Text(
                          esEdicion
                              ? 'GUARDAR CAMBIOS'
                              : 'REGISTRAR BOUTIQUE',
                          style: AppTypography.button,
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
