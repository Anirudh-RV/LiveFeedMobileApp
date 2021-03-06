package com.example.paras.recognitioncam;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Bundle;
import android.support.v4.view.GestureDetectorCompat;
import android.support.v7.app.ActionBar;
import android.support.v7.app.AppCompatActivity;
import android.view.ContextMenu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.MotionEvent;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class EventsActivity extends AppCompatActivity {

    private int currentApiVersion;
    float x1,y1;
    float x2,y2;

    // This textview is used to display swipe or tap status info.
    private TextView textView = null;

    // This is the gesture detector compat instance.
    private GestureDetectorCompat gestureDetectorCompat = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_events);
        currentApiVersion = Build.VERSION.SDK_INT;
        ActionBar actionBar = getSupportActionBar();
        actionBar.hide();



        AsyncTask.execute(new Runnable() {
            @Override
            public void run() {
                //TODO your background code
                currentApiVersion = Build.VERSION.SDK_INT;

                final int flags = View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY;

                // This work only for android 4.4+
                if(currentApiVersion >= Build.VERSION_CODES.KITKAT)
                {

                    getWindow().getDecorView().setSystemUiVisibility(flags);

                    // Code below is to handle presses of Volume up or Volume down.
                    // Without this, after pressing volume buttons, the navigation bar will
                    // show up and won't hide
                    final View decorView = getWindow().getDecorView();
                    decorView
                            .setOnSystemUiVisibilityChangeListener(new View.OnSystemUiVisibilityChangeListener()
                            {

                                @Override
                                public void onSystemUiVisibilityChange(int visibility)
                                {
                                    if((visibility & View.SYSTEM_UI_FLAG_FULLSCREEN) == 0)
                                    {
                                        decorView.setSystemUiVisibility(flags);
                                    }
                                }
                            });
                }
            }
        });


    }


    @SuppressLint("NewApi")
    @Override
    public void onWindowFocusChanged(boolean hasFocus)
    {
        super.onWindowFocusChanged(hasFocus);
        if(currentApiVersion >= Build.VERSION_CODES.KITKAT && hasFocus)
        {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        }
    }

}
