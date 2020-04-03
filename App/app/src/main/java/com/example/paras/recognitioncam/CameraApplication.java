package com.example.paras.recognitioncam;

/**
 * Created by Paras on 30-11-2018.
 */

import android.app.Application;
import android.os.StrictMode;

public final class CameraApplication extends Application
{
    public CameraApplication()
    {
        super();
        StrictMode.setThreadPolicy(new StrictMode.ThreadPolicy.Builder()
                .detectDiskReads()
                .detectDiskWrites()
                .detectNetwork()
                .penaltyLog()
                .build());
        StrictMode.setVmPolicy(new StrictMode.VmPolicy.Builder()
                .detectLeakedSqlLiteObjects()
                .penaltyLog()
                .build());
    } // constructor()
}