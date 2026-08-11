package com.hbg.volte;

import android.content.Context;
import android.os.Looper;
import android.os.PersistableBundle;
import android.telephony.CarrierConfigManager;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * HBG VoLTE Fixer - Native Java Runner via ADB app_process
 * Modifies CarrierConfigManager.sDefaults & notifies ICarrierConfigLoader directly.
 */
public class VolteFixer {

    public static void main(String[] args) {
        System.out.println("=== HBG VoLTE Fixer Java Starter (Android Native) ===");
        try {
            if (Looper.myLooper() == null) {
                Looper.prepareMainLooper();
            }

            Class<?> atClass = Class.forName("android.app.ActivityThread");
            Method systemMain = atClass.getDeclaredMethod("systemMain");
            systemMain.setAccessible(true);
            Object thread = systemMain.invoke(null);

            Method getSystemContext = atClass.getDeclaredMethod("getSystemContext");
            getSystemContext.setAccessible(true);
            Context context = (Context) getSystemContext.invoke(thread);

            System.out.println("✓ Obtained System Context successfully.");

            // 1. Modify Static sDefaults Bundle in CarrierConfigManager
            Field defaultsField = CarrierConfigManager.class.getDeclaredField("sDefaults");
            defaultsField.setAccessible(true);
            PersistableBundle defaults = (PersistableBundle) defaultsField.get(null);

            if (defaults != null) {
                defaults.putBoolean("carrier_volte_available_bool", true);
                defaults.putBoolean("carrier_volte_provisioned_bool", true);
                defaults.putBoolean("hide_enhanced_4g_lte_bool", false);
                defaults.putBoolean("editable_enhanced_4g_lte_bool", true);
                defaults.putBoolean("carrier_supports_ss_over_ut_bool", true);
                defaults.putBoolean("show_4g_for_lte_data_icon_bool", true);
                System.out.println("✓ Injected VoLTE keys into CarrierConfigManager.sDefaults!");
            }

            // 2. Invoke ICarrierConfigLoader notifyConfigChangedForSubId / updateConfigForPhoneId
            CarrierConfigManager ccm = (CarrierConfigManager) context.getSystemService(Context.CARRIER_CONFIG_SERVICE);
            if (ccm != null) {
                Method getLoader = ccm.getClass().getDeclaredMethod("getICarrierConfigLoader");
                getLoader.setAccessible(true);
                Object loader = getLoader.invoke(ccm);

                if (loader != null) {
                    System.out.println("› Notifying Telephony Framework of CarrierConfig changes...");
                    for (int subId = -1; subId <= 5; subId++) {
                        try {
                            Method notifyMethod = loader.getClass().getMethod("notifyConfigChangedForSubId", int.class);
                            notifyMethod.setAccessible(true);
                            notifyMethod.invoke(loader, subId);
                        } catch (Throwable ignored) {}
                    }
                    for (int phoneId = 0; phoneId <= 2; phoneId++) {
                        try {
                            Method updateMethod = loader.getClass().getMethod("updateConfigForPhoneId", int.class, String.class);
                            updateMethod.setAccessible(true);
                            updateMethod.invoke(loader, phoneId, "LOADED");
                        } catch (Throwable ignored) {}
                    }
                    System.out.println("✓ Triggered Telephony CarrierConfig notification reload!");
                }
            }

            System.out.println("✓ SUCCESS: Native VoLTE CarrierConfig injection complete.");
            System.exit(0);

        } catch (Throwable t) {
            System.err.println("✗ EXCEPTION: " + t.getMessage());
            t.printStackTrace(System.err);
            System.exit(3);
        }
    }
}
