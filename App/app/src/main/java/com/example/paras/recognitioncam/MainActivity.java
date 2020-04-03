package com.example.paras.recognitioncam;

import android.Manifest;
import android.app.Activity;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.PowerManager;
import android.preference.PreferenceManager;
import android.support.v4.app.ActivityCompat;
import android.support.v7.app.AlertDialog;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import org.apache.http.HttpResponse;
import org.apache.http.NameValuePair;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.entity.UrlEncodedFormEntity;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.message.BasicNameValuePair;


import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import java.net.ProtocolException;
import java.util.ArrayList;
import java.util.Calendar;
import com.android.volley.AuthFailureError;
import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;

import org.apache.http.HttpResponse;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.impl.client.DefaultHttpClient;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.MalformedURLException;
import java.net.NetworkInterface;
import java.net.URL;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.Map;
import com.android.volley.AuthFailureError;
import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;

import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;


public final class MainActivity extends Activity
        implements SurfaceHolder.Callback
{
    private static final String TAG = MainActivity.class.getSimpleName();

    private static final String WAKE_LOCK_TAG = "RC Scanner";
    private final int REQUEST_CAMERA = 1;

    private static final String PREF_CAMERA = "camera";
    private static final int PREF_CAMERA_INDEX_DEF = 0;
    private static final String PREF_FLASH_LIGHT = "flash_light";
    private static final boolean PREF_FLASH_LIGHT_DEF = false;
    private static final String PREF_PORT = "port";
    private static final int PREF_PORT_DEF = 8080;
    private static final String PREF_JPEG_SIZE = "size";
    private static final String PREF_JPEG_QUALITY = "jpeg_quality";
    private static final int PREF_JPEG_QUALITY_DEF = 30;
    private static final int PREF_PREVIEW_SIZE_INDEX_DEF = 0;
    private static final String LOGTAG = "";
    private WebView webView;

    private boolean mRunning = false;
    private boolean mPreviewDisplayCreated = false;
    private SurfaceHolder mPreviewDisplay = null;
    private CameraStream mCameraStreamer = null;

    private String mIpAddress = "";
    private int mCameraIndex = PREF_CAMERA_INDEX_DEF;
    private boolean mUseFlashLight = PREF_FLASH_LIGHT_DEF;
    private int mPort = PREF_PORT_DEF;
    private int mJpegQuality = PREF_JPEG_QUALITY_DEF;
    private int mPrevieSizeIndex = PREF_PREVIEW_SIZE_INDEX_DEF;
    private TextView mIpAddressView = null;
    private LoadPreferencesTask mLoadPreferencesTask = null;
    private SharedPreferences mPrefs = null;
    private MenuItem mSettingsMenuItem = null;
    private PowerManager.WakeLock mWakeLock = null;
    RequestQueue requestQueue;
    String server_url1 = "http://172.20.10.3:8000/mobilescan";
    String val;
    String JsonURL = "https://api.thingspeak.com/channels/630359/feeds.json?api_key=JVC94MELDXSWISI4&results=1";
    String data = "";
    int counttoast = 0;
    Boolean whileval = true;
    public MainActivity()
    {
        super();
    }

    @Override
    protected void onCreate(final Bundle savedInstanceState)
    {


        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        new LoadPreferencesTask().execute();


        // start


        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            // Check Permissions Now
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.CAMERA},
                    REQUEST_CAMERA);
        }


        // end


        mPreviewDisplay = ((SurfaceView) findViewById(R.id.camera)).getHolder();
        mPreviewDisplay.setType(SurfaceHolder.SURFACE_TYPE_PUSH_BUFFERS);
        mPreviewDisplay.addCallback(this);

        mIpAddress = tryGetIpV4Address();
        mIpAddressView = (TextView) findViewById(R.id.ip_address);
        updatePrefCacheAndUi();

        final PowerManager powerManager =
                (PowerManager) getSystemService(POWER_SERVICE);
        mWakeLock = powerManager.newWakeLock(PowerManager.SCREEN_DIM_WAKE_LOCK,
                WAKE_LOCK_TAG);

        webView = (WebView) findViewById(R.id.webviewLiveDisplay);
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl("http://192.168.1.8:5000/");

    }

    public void refresh(View v)
    {
        // do something
        webView.loadUrl("http://192.168.1.8:5000/");
    }

    @Override
    protected void onResume()
    {

        super.onResume();


        mRunning = true;

        if (mPrefs != null)
        {
            mPrefs.registerOnSharedPreferenceChangeListener(
                    mSharedPreferenceListener);
        } // if
        updatePrefCacheAndUi();
        tryStartCameraStreamer();
        mWakeLock.acquire();
    }

    @Override
    protected void onPause()
    {
        mWakeLock.release();
        super.onPause();
        mRunning = false;
        if (mPrefs != null)
        {
            mPrefs.unregisterOnSharedPreferenceChangeListener(
                    mSharedPreferenceListener);
        }
        ensureCameraStreamerStopped();
    }

    @Override
    public void surfaceChanged(final SurfaceHolder holder, final int format,
                               final int width, final int height)
    {
        // Ingored
    }

    @Override
    public void surfaceCreated(final SurfaceHolder holder)
    {
        mPreviewDisplayCreated = true;
        tryStartCameraStreamer();
    }

    @Override
    public void surfaceDestroyed(final SurfaceHolder holder)
    {
        mPreviewDisplayCreated = false;
        ensureCameraStreamerStopped();
    }

    public void CheckJason() {
        requestQueue = Volley.newRequestQueue(MainActivity.this);
        final String[] fields1 = new String[1];
        // Casts results into the TextView found within the main layout XML with id jsonData

        // Creating the JsonObjectRequest class called obreq, passing required parameters:
        //GET is used to fetch data from the server, JsonURL is the URL to be fetched from.
        JsonObjectRequest obreq = new JsonObjectRequest(Request.Method.GET, JsonURL,
                // The third parameter Listener overrides the method onResponse() and passes
                //JSONObject as a parameter
                new Response.Listener<JSONObject>() {

                    // Takes the response from the JSON request
                    @Override
                    public void onResponse(JSONObject response) {
                        try {
                            // JSONObject obj = response.getJSONObject("feeeds");
                            // Retrieves the string labeled "colorName" and "description" from
                            //the response JSON Object
                            //and converts them into javascript objects
                            JSONArray arr = response.getJSONArray("feeds");
                            //  int stat = arr.getInt(2);
                            for (int i = 0; i < arr.length(); i++) {
                                JSONObject jsonobject = arr.getJSONObject(i);
                                val = jsonobject.getString("field1");
                            }

                            // Adds strings from object to the "data" string
                            data += "working? " + val + "\n";

                            int chec = Integer.parseInt(val);
                            if (chec == 1)
                            {
                                Toast.makeText(getApplicationContext(),"DONE SCANNING : flag: "+val,Toast.LENGTH_LONG).show();
                                Thread thread = new Thread() {
                                    @Override
                                    public void run() {
                                        // Creating HTTP client
                                        HttpClient httpClient = new DefaultHttpClient();
                                        // Creating HTTP Post
                                        HttpPost httpPost = new HttpPost(
                                                "https://api.thingspeak.com/update?api_key=EPO4PIK2ZNDJC9LL&field1=0");

                                        try {
                                            HttpResponse response = httpClient.execute(httpPost);

                                            // writing response to log
                                            Log.d("Http Response:", response.toString());
                                        } catch (ClientProtocolException e) {
                                            // writing exception to log
                                            e.printStackTrace();
                                        } catch (IOException e) {
                                            // writing exception to log
                                            e.printStackTrace();

                                        }

                                    }
                                };
                                thread.start();
                                whileval = false;
                                Intent intent = new Intent(MainActivity.this,EventsActivity.class);// New activity
                                intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
                                startActivity(intent);
                                finish();

                            }
                            counttoast = 1;
                            // Adds the data string to the TextView "results"

                        }
                        // Try and catch are included to handle any errors due to JSON
                        catch (JSONException e) {
                            // If an error occurs, this prints the error to the log
                            e.printStackTrace();
                        }
                    }
                },
                // The final parameter overrides the method onErrorResponse() and passes VolleyError
                //as a parameter
                new Response.ErrorListener() {
                    @Override
                    // Handles errors that occur due to Volley
                    public void onErrorResponse(VolleyError error) {
                        Log.e("Volley", "Error");
                    }
                }
        );
        // Adds the JSON object request "obreq" to the request queue
        requestQueue.add(obreq);
    }

    private void tryStartCameraStreamer()
    {
        if (mRunning && mPreviewDisplayCreated && mPrefs != null)
        {
            mCameraStreamer = new CameraStream(mCameraIndex, mUseFlashLight, mPort,
                    mPrevieSizeIndex, mJpegQuality, mPreviewDisplay);
            mCameraStreamer.start();
            // starting here :

            Thread thread = new Thread() {
                @Override
                public void run() {
                    // Creating HTTP client

                    HttpClient httpClient = new DefaultHttpClient();
                    // Creating HTTP Post
                    HttpPost httpPost = new HttpPost(
                            "http://172.20.10.3:8000/mobilescan");

                    try {
                        HttpResponse response = httpClient.execute(httpPost);

                        // writing response to log
                        Log.d("Http Response:", response.toString());
                    } catch (ClientProtocolException e) {
                        // writing exception to log
                        e.printStackTrace();
                    } catch (IOException e) {
                        // writing exception to log
                        e.printStackTrace();

                    }

                }
            };
            thread.start();


            // two :
            Thread thread1 = new Thread() {
                @Override
                public void run() {

                    while(whileval){
                        CheckJason();
                        try {
                            Thread.sleep(1000);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                }
            };
            thread1.start();
        }
    }

    private void ensureCameraStreamerStopped()
    {
        if (mCameraStreamer != null)
        {
            mCameraStreamer.stop();
            mCameraStreamer = null;
        }
    }

    @Override
    public boolean onCreateOptionsMenu(final Menu menu)
    {
        super.onCreateOptionsMenu(menu);
        //mSettingsMenuItem = menu.add(R.string.settings);
        mSettingsMenuItem.setIcon(android.R.drawable.ic_menu_manage);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(final MenuItem item)
    {
        if (item != mSettingsMenuItem)
        {
            return super.onOptionsItemSelected(item);
        } // if
        startActivity(new Intent(this, Preferences.class));
        return true;
    } // onOptionsItemSelected(MenuItem)

    private final class LoadPreferencesTask
            extends AsyncTask<Void, Void, SharedPreferences>
    {
        private LoadPreferencesTask()
        {
            super();
        } // constructor()

        @Override
        protected SharedPreferences doInBackground(final Void... noParams)
        {
            return PreferenceManager.getDefaultSharedPreferences(
                    MainActivity.this);
        }

        @Override
        protected void onPostExecute(final SharedPreferences prefs)
        {
            MainActivity.this.mPrefs = prefs;
            prefs.registerOnSharedPreferenceChangeListener(
                    mSharedPreferenceListener);
            updatePrefCacheAndUi();
            tryStartCameraStreamer();
        }
    }

    private final SharedPreferences.OnSharedPreferenceChangeListener mSharedPreferenceListener =
            new SharedPreferences.OnSharedPreferenceChangeListener()
            {
                @Override
                public void onSharedPreferenceChanged(final SharedPreferences prefs,
                                                      final String key)
                {
                    updatePrefCacheAndUi();
                } // onSharedPreferenceChanged(SharedPreferences, String)

            }; // mSharedPreferencesListener

    private final int getPrefInt(final String key, final int defValue)
    {
        // We can't just call getInt because the preference activity
        // saves everything as a string.
        try
        {
            return Integer.parseInt(mPrefs.getString(key, null /* defValue */));
        } // try
        catch (final NullPointerException e)
        {
            return defValue;
        } // catch
        catch (final NumberFormatException e)
        {
            return defValue;
        } // catch
    } // getPrefInt(String, int)

    private final void updatePrefCacheAndUi()
    {
        mCameraIndex = getPrefInt(PREF_CAMERA, PREF_CAMERA_INDEX_DEF);
        if (hasFlashLight())
        {
            if (mPrefs != null)
            {
                mUseFlashLight = mPrefs.getBoolean(PREF_FLASH_LIGHT,
                        PREF_FLASH_LIGHT_DEF);
            } // if
            else
            {
                mUseFlashLight = PREF_FLASH_LIGHT_DEF;
            } // else
        } //if
        else
        {
            mUseFlashLight = false;
        } // else


        mPort = getPrefInt(PREF_PORT, PREF_PORT_DEF);
        if (mPort < 1024)
        {
            mPort = 1024;
        } // if
        else if (mPort > 65535)
        {
            mPort = 65535;
        } // else if

        mPrevieSizeIndex = getPrefInt(PREF_JPEG_SIZE, PREF_PREVIEW_SIZE_INDEX_DEF);
        mJpegQuality = getPrefInt(PREF_JPEG_QUALITY, PREF_JPEG_QUALITY_DEF);
        // The JPEG quality must be in the range [0 100]
        if (mJpegQuality < 0)
        {
            mJpegQuality = 0;
        } // if
        else if (mJpegQuality > 100)
        {
            mJpegQuality = 100;
        } // else if
        mIpAddressView.setText("http://" + mIpAddress + ":" + mPort + "/");
    } // updatePrefCacheAndUi()

    private boolean hasFlashLight()
    {
        return getPackageManager().hasSystemFeature(
                PackageManager.FEATURE_CAMERA_FLASH);
    } // hasFlashLight()

    private static String tryGetIpV4Address()
    {
        try
        {
            final Enumeration<NetworkInterface> en =
                    NetworkInterface.getNetworkInterfaces();
            while (en.hasMoreElements())
            {
                final NetworkInterface intf = en.nextElement();
                final Enumeration<InetAddress> enumIpAddr =
                        intf.getInetAddresses();
                while (enumIpAddr.hasMoreElements())
                {
                    final  InetAddress inetAddress = enumIpAddr.nextElement();
                    if (!inetAddress.isLoopbackAddress())
                    {
                        final String addr = inetAddress.getHostAddress().toUpperCase();
                        if(inetAddress instanceof Inet4Address)
                        {
                            Log.w(LOGTAG, "local IP: "+ addr);
                            return addr;
                        }
                    } // if
                } // while
            } // for
        } // try
        catch (final Exception e)
        {
            // Ignore
        } // catch
        return null;
    } // tryGetIpV4Address()

} // class MainActivity

