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
import java.util.concurrent.atomic.AtomicInteger

class MainActivity : FlutterActivity() {
    companion object {
        private const val CANAL_METODO = "com.ecommerce.ec_mobile/notificaciones"
        private const val CANAL_NOTIF_ID = "fashionstore_notificaciones"
        private const val CANAL_NOTIF_NOMBRE = "Notificaciones Fashion Store"
        private const val CODIGO_SOLICITUD_NOTIF = 4109
        private const val EXTRA_PANTALLA = "fs_push_pantalla"
        private const val EXTRA_ID_REF = "fs_push_id"
        private val contadorNotif = AtomicInteger(1000)
    }

    private var resultadoPermisoPendiente: MethodChannel.Result? = null
    private var canalMetodo: MethodChannel? = null
    private var destinoInicialPendiente: Map<String, String>? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        asegurarCanalNotificaciones()
        capturarDestinoDeIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        val destino = extraerDestinoDeIntent(intent)
        if (destino != null) {
            canalMetodo?.invokeMethod("notificacionTocada", destino)
        }
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        canalMetodo = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CANAL_METODO).apply {
            setMethodCallHandler { call, result ->
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
                        val pantalla = call.argument<String>("pantalla")
                        val idRef = call.argument<String>("id")
                        result.success(mostrarNotificacionSistema(titulo, cuerpo, pantalla, idRef))
                    }
                    "consumirDestinoInicial" -> {
                        val pendiente = destinoInicialPendiente
                        destinoInicialPendiente = null
                        result.success(pendiente)
                    }
                    "abrirAjustesNotificaciones" -> {
                        abrirAjustesSistema()
                        result.success(true)
                    }
                    else -> result.notImplemented()
                }
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

    private fun capturarDestinoDeIntent(intent: Intent?) {
        val destino = extraerDestinoDeIntent(intent)
        if (destino != null) {
            destinoInicialPendiente = destino
        }
    }

    private fun extraerDestinoDeIntent(intent: Intent?): Map<String, String>? {
        val pantalla = intent?.getStringExtra(EXTRA_PANTALLA) ?: return null
        val idRef = intent.getStringExtra(EXTRA_ID_REF) ?: ""
        return mapOf("pantalla" to pantalla, "id" to idRef)
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

    private fun mostrarNotificacionSistema(
        titulo: String,
        cuerpo: String,
        pantalla: String?,
        idRef: String?
    ): Boolean {
        return try {
            asegurarCanalNotificaciones()
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
                ?: return false

            val notifId = contadorNotif.incrementAndGet()
            val intent = Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
                if (!pantalla.isNullOrBlank()) {
                    putExtra(EXTRA_PANTALLA, pantalla)
                }
                if (!idRef.isNullOrBlank()) {
                    putExtra(EXTRA_ID_REF, idRef)
                }
            }
            val flags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            } else {
                PendingIntent.FLAG_UPDATE_CURRENT
            }
            val pendingIntent = PendingIntent.getActivity(this, notifId, intent, flags)

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
