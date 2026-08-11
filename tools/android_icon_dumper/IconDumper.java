import android.content.pm.ApplicationInfo;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;

import java.io.File;
import java.io.FileOutputStream;
import java.lang.reflect.Method;

/**
 * Dump launcher icon via PackageManager (same as on-screen icon).
 * ActivityThread via reflection (hidden API, not in compile-time android.jar).
 */
public class IconDumper {
    private static final int OUT_PX = 192;
    private static final float CONTENT_FILL = 0.86f;

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("USAGE: IconDumper <outDir> <package> [package2 ...]");
            System.exit(1);
        }
        String outDir = args[0];
        if (!outDir.endsWith("/")) {
            outDir = outDir + "/";
        }
        File dir = new File(outDir);
        if (!dir.exists() && !dir.mkdirs()) {
            System.err.println("Cannot create " + outDir);
            System.exit(3);
        }

        int ok = 0;
        int fail = 0;
        try {
            Object pm = obtainPackageManager();

            for (int i = 1; i < args.length; i++) {
                String pkg = args[i];
                if (pkg == null || pkg.isEmpty()) {
                    continue;
                }
                String safe = pkg.replace('.', '_');
                String outPath = outDir + safe + ".png";
                try {
                    dumpIcon(pm, pkg, outPath);
                    System.out.println("OK " + pkg);
                    ok++;
                } catch (Throwable t) {
                    System.err.println("FAIL " + pkg + " " + t.getMessage());
                    fail++;
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
            System.exit(2);
        }
        System.out.println("DONE ok=" + ok + " fail=" + fail);
        System.exit(fail > 0 && ok == 0 ? 2 : 0);
    }

    private static Object obtainPackageManager() throws Exception {
        Class<?> at = Class.forName("android.app.ActivityThread");
        Method systemMain = at.getDeclaredMethod("systemMain");
        systemMain.setAccessible(true);
        Object thread = systemMain.invoke(null);
        Method getSystemContext = at.getDeclaredMethod("getSystemContext");
        getSystemContext.setAccessible(true);
        Object context = getSystemContext.invoke(thread);
        Method getPm = context.getClass().getMethod("getPackageManager");
        return getPm.invoke(context);
    }

    private static void dumpIcon(Object pm, String pkg, String outPath) throws Exception {
        Method getAppInfo = pm.getClass().getMethod("getApplicationInfo", String.class, int.class);
        ApplicationInfo ai = (ApplicationInfo) getAppInfo.invoke(pm, pkg, 0);
        Method getIcon = pm.getClass().getMethod("getApplicationIcon", ApplicationInfo.class);
        Drawable icon = (Drawable) getIcon.invoke(pm, ai);
        if (icon == null) {
            throw new IllegalStateException("no icon drawable");
        }

        int w = icon.getIntrinsicWidth();
        int h = icon.getIntrinsicHeight();
        if (w <= 0) {
            w = OUT_PX;
        }
        if (h <= 0) {
            h = OUT_PX;
        }

        Bitmap bmp = Bitmap.createBitmap(OUT_PX, OUT_PX, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bmp);
        float pad = OUT_PX * (1f - CONTENT_FILL) / 2f;
        float box = OUT_PX - 2f * pad;
        float scale = Math.min(box / (float) w, box / (float) h);
        float dw = w * scale;
        float dh = h * scale;
        int left = Math.round((OUT_PX - dw) / 2f);
        int top = Math.round((OUT_PX - dh) / 2f);
        icon.setBounds(left, top, left + Math.round(dw), top + Math.round(dh));
        icon.draw(canvas);

        FileOutputStream fos = new FileOutputStream(outPath);
        try {
            if (!bmp.compress(Bitmap.CompressFormat.PNG, 100, fos)) {
                throw new IllegalStateException("compress failed");
            }
            fos.flush();
        } finally {
            fos.close();
        }
    }
}
