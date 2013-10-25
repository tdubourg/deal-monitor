package com.dealmonitor.smssender;

import android.telephony.SmsManager;


import java.io.IOException;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketAddress;
import java.net.UnknownHostException;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.dealmonitor.smssender.R;

import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Process;
// import android.support.v4.app.NotificationCompat;
// import android.support.v4.app.TaskStackBuilder;
import android.util.Log;
import android.widget.Toast;

public class SMSService extends Service {
	public static final String PREFS_NAME = "MyPrefsFile";
	protected static final String LOG_TAG = "SMSService";
	String ipAddress;
	String deviceName;
	private static boolean DBG = false;

	protected void TTextShow(String text) {
		if(!DBG) {
			return;
		}
		Toast.makeText(getApplicationContext(), text, Toast.LENGTH_SHORT)
				.show();
	}

	@Override
	public void onCreate() {
		super.onCreate();
		Log.v(LOG_TAG, "onCreate() launched.");
		HandlerThread thread = new HandlerThread("ServiceStartArguments", Process.THREAD_PRIORITY_BACKGROUND);
		thread.start();

		// Get the HandlerThread's Looper and use it for our Handler
		mServiceLooper = thread.getLooper();
		mServiceHandler = new ServiceHandler(mServiceLooper);
	};

	private Looper mServiceLooper;
	private ServiceHandler mServiceHandler;

	// Handler that receives messages from the thread
	private final class ServiceHandler extends Handler {
		private static final long RETRY_CONNECT_DELAY = 1 * 1000;

//		private static final String IP_ADDR = "192.168.0.13";

		private static final int PORT = 8080;

		private int mId;

		public ServiceHandler(Looper looper) {
			super(looper);
		}

		protected boolean connect() {
			SharedPreferences settings = getSharedPreferences(PREFS_NAME, 0);
			ipAddress = settings.getString("ip_address", "192.168.0.14");
			deviceName = settings.getString("device_name", "not_set_yet");
			
			if (mConnected) {// Only one connection has to be established, if
								// there is already one, then don't do anything
				return true;
			}

			InetAddress addr = null;
			try {
				addr = InetAddress.getByName(ipAddress);
			} catch (UnknownHostException e1) {
				stopAndRelaunchConnection();
				return false;
			}
			Log.v(LOG_TAG, "Trying to connect to (" + addr.toString() + "," + PORT + ")");
			SocketAddress remoteAddr = new InetSocketAddress(addr, PORT);
			mSock = new Socket();
			try {
				mSock.connect(remoteAddr);
			} catch (IOException e1) {
				TTextShow("Socket.connect() error");
				Log.e(LOG_TAG, "Socket connect error\n" + e1.getCause());
				stopAndRelaunchConnection();
				return false;
			}
			postDelayed(new Runnable() {
				
				@Override
				public void run() {
					readUntilDeath();
				}
			}, 100);
			return true;
		}
		
		protected void readUntilDeath() {
			Scanner sc = null;
			try {
				sc = new Scanner(mSock.getInputStream());
			} catch (IOException e1) {
				stopAndRelaunchConnection();
				return;
			}
			// If we want to do some data sending to the server, the following
			// code might help:

			PrintWriter out = null;
			try {
				out = new PrintWriter(mSock.getOutputStream());
			} catch (IOException e1) {
				Log.v(LOG_TAG, "Error instanciating PrintWriter", e1);
			}
			
			out.print(deviceName);
			out.println("@@end@@");
			out.flush();
			sc.nextLine();// Reading the ACK
			Log.v(LOG_TAG, "ACK Received");

			Pattern pattern = Pattern.compile("@@msg@@(.+)@@phone@@([0-9]+)", Pattern.CASE_INSENSITIVE | Pattern.DOTALL | Pattern.MULTILINE);
			Pattern patternStartOfNotif = Pattern.compile("@@notif@@");
			Pattern patternEndOfNotif = Pattern.compile("@@end@@");


			try {
				// Start the never ending story !
				for (;;) {
					String str = sc.nextLine();
					Log.v(LOG_TAG, str);
					Matcher m = patternStartOfNotif.matcher(str);
					if (m.find()) {
						Log.v(LOG_TAG, "Notif frame began, waiting for the notif content");
						String frame = "";
						while(sc.hasNextLine()) {
							Log.v(LOG_TAG, "has next line...");
							String line = sc.nextLine();
							Log.v(LOG_TAG, "receiving" + line);
							if (!patternEndOfNotif.matcher(line).find()) {
								frame += line;
							} else {
								break;
							}
						}
						// sc.nextLine(); // empty the buffer by reading the end of frame
						Log.v(LOG_TAG, "Notification received is:" + frame);
						m = pattern.matcher(frame);
						if (m.find()) {
							Log.v(LOG_TAG, "MATCHES!!");
							Log.v(LOG_TAG, m.group(1) + m.group(2));
							SmsManager smsManager = SmsManager.getDefault();
                			smsManager.sendTextMessage(m.group(2), null, m.group(1), null, null);
							Log.v(LOG_TAG, "SMS Sent!");
						} else {
							Log.v(LOG_TAG, "DOES NOT MATCH!!");
						}
					}
					// if (m.find()) {
						// notif(m.group(1), m.group(4));
					// }
					Log.v(LOG_TAG, "received: " + str);
				}
			} catch (Exception e1) {
				Log.v(LOG_TAG, "Exception raised", e1);
				stopAndRelaunchConnection();
				return;
			}
		}

		boolean mConnected = false;

		Socket mSock = new Socket();

		@Override
		public void handleMessage(Message msg) {
			if(!mConnected) {
				connect();
			}
		}

		private void stopAndRelaunchConnection() {
			try {
				mSock.close();
			} catch(Exception e) {}//don't care
			mConnected = false;
			postDelayed(new Runnable() {
				public void run() {
					connect();
				}
			}, RETRY_CONNECT_DELAY);

		}

		// NotificationCompat.Builder mBuilder = new NotificationCompat.Builder(
		// 		getApplicationContext()).setSmallIcon(R.drawable.ic_launcher);

		// private void notif(String msg, String url) {
		// 	mBuilder.setContentTitle("GHome").setContentText(
		// 			msg);
		// 	// Creates an explicit intent for an Activity in your app
		// 	if(null == url) {
		// 		url = "http://" + ipAddress + "/";
		// 	}
		// 	Intent resultIntent = new Intent(Intent.ACTION_VIEW, 
		// 		       Uri.parse(url));
		//     PendingIntent resultPendingIntent = PendingIntent.getActivity(getApplicationContext(), 0, resultIntent, 0);
		// 	mBuilder.setContentIntent(resultPendingIntent);
		// 	NotificationManager mNotificationManager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
		// 	// mId allows you to update the notification later on.
		// 	mNotificationManager.notify(mId++, mBuilder.build());

		// }
	}

	@Override
	public void onDestroy() {
		super.onDestroy();
		Log.v(LOG_TAG, "onDestroy() launched.");
		TTextShow("SMSService onDestroy()");
	};

	@Override
	public IBinder onBind(Intent arg0) {
		Log.v(LOG_TAG, "onBind() launched.");
		TTextShow("SMSService onBind()");
		return null;
	}

	@Override
	public int onStartCommand(Intent intent, int flags, int startId) {
		Log.v(LOG_TAG, "onStartCommand() launched.");
		Message msg = mServiceHandler.obtainMessage();
		msg.arg1 = flags;
		msg.arg2 = startId;
		mServiceHandler.sendMessage(msg);

		// If we get killed, after returning from here, restart
		return START_STICKY;
	}

}
