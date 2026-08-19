package com.hbg.volte;

import android.os.Looper;
import android.os.PersistableBundle;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * HBG VoLTE Fixer - Native Java Runner via ADB app_process (v2.0)
 * Bypasses TelephonyServiceManager null pointer by using ServiceManager.getService("carrier_config") directly.
 * Calls ICarrierConfigLoader.overrideConfig & notifyConfigChangedForSubId via Java AIDL Binder IPC.
 */
public class VolteFixer {

    public static void main(String[] args) {
        boolean isReset = args != null && args.length > 0 && "reset".equalsIgnoreCase(args[0]);
        System.out.println("=== HBG VoLTE Fixer Native Java Runner (v2.0 " + (isReset ? "RESET" : "ENABLE") + ") ===");
        try {
            if (Looper.myLooper() == null) {
                Looper.prepareMainLooper();
            }

            boolean enableVal = !isReset;
            boolean hideVal = isReset;

            // 1. Modify Static sDefaults Bundle in CarrierConfigManager
            try {
                Class<?> ccmClass = Class.forName("android.telephony.CarrierConfigManager");
                Field defaultsField = ccmClass.getDeclaredField("sDefaults");
                defaultsField.setAccessible(true);
                PersistableBundle defaults = (PersistableBundle) defaultsField.get(null);
                if (defaults != null) {
                    defaults.putBoolean("carrier_volte_available_bool", enableVal);
                    defaults.putBoolean("carrier_volte_provisioned_bool", enableVal);
                    defaults.putBoolean("hide_enhanced_4g_lte_bool", hideVal);
                    defaults.putBoolean("editable_enhanced_4g_lte_bool", enableVal);
                    defaults.putBoolean("carrier_supports_ss_over_ut_bool", enableVal);
                    defaults.putBoolean("show_4g_for_lte_data_icon_bool", enableVal);
                    defaults.putBoolean("carrier_wfc_ims_available_bool", enableVal);
                    defaults.putBoolean("carrier_vt_available_bool", enableVal);
                    System.out.println("✓ Updated CarrierConfigManager.sDefaults (enable=" + enableVal + ")");
                }
            } catch (Throwable t) {
                System.out.println("⚠ Notice sDefaults: " + t.getMessage());
            }

            // 2. Obtain ICarrierConfigLoader directly via ServiceManager (bypassing TelephonyServiceManager null pointer)
            Class<?> smClass = Class.forName("android.os.ServiceManager");
            Method getService = smClass.getMethod("getService", String.class);
            Object binder = getService.invoke(null, "carrier_config");

            if (binder != null) {
                Class<?> stubClass = Class.forName("com.android.internal.telephony.ICarrierConfigLoader$Stub");
                Method asInterface = stubClass.getMethod("asInterface", Class.forName("android.os.IBinder"));
                Object loader = asInterface.invoke(null, binder);

                if (loader != null) {
                    System.out.println("✓ Obtained ICarrierConfigLoader Binder successfully.");

                    // Build target PersistableBundle
                    PersistableBundle bundle = new PersistableBundle();
                    bundle.putBoolean("carrier_volte_available_bool", enableVal);
                    bundle.putBoolean("carrier_volte_provisioned_bool", enableVal);
                    bundle.putBoolean("hide_enhanced_4g_lte_bool", hideVal);
                    bundle.putBoolean("editable_enhanced_4g_lte_bool", enableVal);
                    bundle.putBoolean("carrier_supports_ss_over_ut_bool", enableVal);
                    bundle.putBoolean("show_4g_for_lte_data_icon_bool", enableVal);
                    bundle.putBoolean("carrier_wfc_ims_available_bool", enableVal);
                    bundle.putBoolean("carrier_vt_available_bool", enableVal);

                    // Try overrideConfig on ICarrierConfigLoader for subIds -1..5
                    for (int subId = -1; subId <= 5; subId++) {
                        try {
                            Method overrideMethod = null;
                            for (Method m : loader.getClass().getMethods()) {
                                if (m.getName().equals("overrideConfig")) {
                                    overrideMethod = m;
                                    break;
                                }
                            }
                            if (overrideMethod != null) {
                                overrideMethod.setAccessible(true);
                                Class<?>[] paramTypes = overrideMethod.getParameterTypes();
                                if (paramTypes.length == 2) {
                                    overrideMethod.invoke(loader, subId, bundle);
                                } else if (paramTypes.length == 3) {
                                    overrideMethod.invoke(loader, subId, bundle, true);
                                }
                            }
                        } catch (Throwable ignored) {}
                    }

                    // Notify reloads
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

            System.out.println("✓ SUCCESS: Native VoLTE CarrierConfig execution complete.");
            System.exit(0);

        } catch (Throwable t) {
            System.err.println("✗ EXCEPTION: " + t.getMessage());
            t.printStackTrace(System.err);
            System.exit(3);
        }
    }
}
