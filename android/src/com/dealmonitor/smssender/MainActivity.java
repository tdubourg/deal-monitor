package com.dealmonitor.smssender;

import android.app.Activity;
import android.os.Bundle;
import android.app.Activity;
import android.telephony.SmsManager;
import android.widget.Toast;

public class MainActivity extends Activity
{
    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

              try {
                SmsManager smsManager = SmsManager.getDefault();
                smsManager.sendTextMessage("", null, "Ceci est un sms de test envoye depuis l'application :)", null, null);
                Toast.makeText(getApplicationContext(), "SMS Sent!",
                            Toast.LENGTH_LONG).show();
              } catch (Exception e) {
                Toast.makeText(getApplicationContext(),
                    "SMS faild, please try again later!",
                    Toast.LENGTH_LONG).show();
                e.printStackTrace();
              }
    }
}
