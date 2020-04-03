package com.example.paras.recognitioncam;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.webkit.WebView;

public class DisplayWeb extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebView myWebView = new WebView(DisplayWeb.this);
        setContentView(myWebView);

        myWebView.loadUrl("http://172.20.10.3:8000/index");

    }
}
