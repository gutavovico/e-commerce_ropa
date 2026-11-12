package com.ecommerce.ec_mobile

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    companion object {
        private const val CANAL_METODO = "com.ecommerce.ec_mobile/notificaciones"
        private const val CANAL_NOTIF_ID = "fashionstore_notificaciones"
        private const val CANAL_NOTIF_NOMBRE = "Notificaciones Fashion Store"
        private const val CODIGO_SOLICITUD_NOTIF = 4109
    }

    private var resultadoPermisoPendiente: MethodChannel.Result? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        asegurarCanalNotificaciones()
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CANAL_METODO)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "verificarPermiso" -> {
                        result.success(tienePermisoNotificaciones())
                    }
                    "solicitarPermiso" -> {
                        asegurarCanalNotificaciones()
                        if (Build.VERSION.SDK_INT >= 33) {
                            if (tienePermisoNotificaciones()) {
                                result.success(true)
                            } else {
                                resultadoPermisoPendiente?.success(false)
                                resultadoPermisoPendiente = result
                                requestPermissions(
                                    arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                                    CODIGO_SOLICITUD_NOTIF
                                )
                            }
                        } else {
                            result.success(tienePermisoNotificaciones())
                        }
                    }
                    "mostrarNotificacionLocal" -> {
                        val titulo = call.argument<String>("titulo") ?: "Fashion Store"
                        val cuerpo = call.argument<String>("cuerpo") ?: ""
                        result.success(mostrarNotificacionSistema(titulo, cuerpo))
                    }
                    "abrirAjustesNotificaciones" -> {
                        abrirAjustesSistema()
                        result.success(true)
                    }
                    else -> result.notImplemented()
                }
            }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == CODIGO_SOLICITUD_NOTIF) {
            val concedido = grantResults.isNotEmpty() &&
                grantResults[0] == PackageManager.PERMISSION_GRANTED
            resultadoPermisoPendiente?.success(concedido)
            resultadoPermisoPendiente = null
        }
    }

    private fun tienePermisoNotificaciones(): Boolean {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
            ?: return false
        val canalHabilitado = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            manager.areNotificationsEnabled()
        } else {
            true
        }
        if (Build.VERSION.SDK_INT >= 33) {
            val runtimeGranted = checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) ==
                PackageManager.PERMISSION_GRANTED
            return runtimeGranted && canalHabilitado
        }
        return canalHabilitado
    }

    private fun asegurarCanalNotificaciones() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
                ?: return
            val existente = manager.getNotificationChannel(CANAL_NOTIF_ID)
            if (existente == null) {
                val canal = NotificationChannel(
                    CANAL_NOTIF_ID,
                    CANAL_NOTIF_NOMBRE,
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "Avisos de reservas, pedidos, pagos y asistente de estilo"
                    enableVibration(true)
                }
                manager.createNotificationChannel(canal)
            }
        }
    }

    private fun mostrarNotificacionSistema(titulo: String, cuerpo: String): Boolean {
        return try {
            asegurarCanalNotificaciones()
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
                ?: return false

            val intent = Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
            val flags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            } else {
                PendingIntent.FLAG_UPDATE_CURRENT
            }
            val pendingIntent = PendingIntent.getActivity(this, 0, intent, flags)

            val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                Notification.Builder(this, CANAL_NOTIF_ID)
            } else {
                @Suppress("DEPRECATION")
                Notification.Builder(this)
            }

            val notif = builder
                .setSmallIcon(applicationInfo.icon)
                .setContentTitle(titulo)
                .setContentText(cuerpo)
                .setStyle(Notification.BigTextStyle().bigText(cuerpo))
                .setAutoCancel(true)
                .setContentIntent(pendingIntent)
                .build()

            val notifId = (System.currentTimeMillis() % Int.MAX_VALUE).toInt()
            manager.notify(notifId, notif)
            true
        } catch (_: Exception) {
            false
        }
    }

    private fun abrirAjustesSistema() {
        val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).apply {
                putExtra(Settings.EXTRA_APP_PACKAGE, packageName)
            }
        } else {
            Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.fromParts("package", packageName, null)
            }
        }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        startActivity(intent)
    }
}
