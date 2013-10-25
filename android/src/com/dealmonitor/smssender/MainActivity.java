package com.dealmonitor.smssender;

import android.app.Activity;
import android.os.Bundle;
import android.app.Activity;
import android.telephony.SmsManager;
import android.widget.Toast;
import android.content.Intent;
import android.util.Log;

public class MainActivity extends Activity
{
    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);
    }

    @Override
    public void onStart(){
        super.onStart();
        Log.v("SMSS", "onStart() of MainActivity. Starting service...");
        startService(new Intent(this, SMSService.class));
    }
}
