package game.emberfall;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.webkit.*;
import android.widget.*;
import androidx.webkit.WebViewAssetLoader;
import androidx.webkit.WebViewCompat;
import androidx.webkit.WebViewFeature;
import java.io.ByteArrayInputStream;
import java.util.Set;
import java.util.Map;
import org.json.JSONObject;

public class MainActivity extends Activity {
    private static final String OFFLINE = "https://appassets.androidplatform.net";
    private WebView web;
    private String activeOrigin = OFFLINE;
    private LinearLayout chooser;
    private boolean messageBridge;
    @Override public void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        showChooser();
    }
    private int dp(int n) {return (int)(n * getResources().getDisplayMetrics().density);}
    private TextView text(String label, int size, int color) {
        TextView t = new TextView(this); t.setText(label); t.setTextSize(size); t.setTextColor(color); t.setPadding(0,dp(6),0,dp(6)); return t;
    }
    private void showChooser() {
        if(web != null) {web.onPause(); web.stopLoading();}
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true); scroll.setBackgroundColor(Color.rgb(16,29,26));
        chooser = new LinearLayout(this); chooser.setOrientation(LinearLayout.VERTICAL); chooser.setPadding(dp(36),dp(20),dp(36),dp(20)); chooser.setGravity(Gravity.CENTER_VERTICAL);
        chooser.addView(text("EMBERFALL",30,0xFFF5D18C));
        chooser.addView(text("Your kingdom, everywhere",18,0xFFF3F0E6));
        chooser.addView(text("Play on this device or connect to your kingdom server.",14,0xFFBFD0C3));
        EditText input = new EditText(this); input.setSingleLine(true); input.setTextSize(16); input.setTextColor(0xFFF3F0E6); input.setHintTextColor(0xFF93A69A); input.setHint("https://your-kingdom.example"); input.setInputType(0x11); input.setText(getPreferences(0).getString("server","")); chooser.addView(input);
        LinearLayout actions = new LinearLayout(this); actions.setOrientation(LinearLayout.HORIZONTAL);
        Button connect = new Button(this); connect.setText("Connect to server"); connect.setOnClickListener(v -> {
            String origin = secureOrigin(input.getText().toString().trim());
            if(origin == null || OFFLINE.equals(origin)) {input.setError("Enter your HTTPS server address without a path."); return;}
            getPreferences(0).edit().putString("server",origin).apply(); loadGame(origin);
        }); actions.addView(connect,new LinearLayout.LayoutParams(0,dp(52),1));
        Button offline = new Button(this); offline.setText("Play on this device"); offline.setOnClickListener(v -> loadGame(OFFLINE)); actions.addView(offline,new LinearLayout.LayoutParams(0,dp(52),1)); chooser.addView(actions);
        chooser.addView(text("Device play stays on this app. Server accounts and purchases require a connected server. Version 5.0.0",12,0xFF93A69A));
        scroll.addView(chooser); setContentView(scroll);
    }
    private String secureOrigin(String value) {
        try {Uri u=Uri.parse(value); if(!"https".equals(u.getScheme()) || u.getHost()==null || u.getUserInfo()!=null || u.getQuery()!=null || u.getFragment()!=null || !(u.getPath()==null || u.getPath().isEmpty() || "/".equals(u.getPath()))) return null;
            return "https://" + u.getEncodedAuthority().toLowerCase(java.util.Locale.ROOT);
        } catch(Exception e) {return null;}
    }
    private boolean trusted(Uri u) {return u != null && activeOrigin.equals(u.getScheme()+"://"+u.getEncodedAuthority());}
    private void external(String value) {
        try {Uri u=Uri.parse(value); if(!"https".equals(u.getScheme()) || u.getHost()==null || u.getUserInfo()!=null) return;
            startActivity(new Intent(Intent.ACTION_VIEW,u).addCategory(Intent.CATEGORY_BROWSABLE));
        } catch(Exception e) {Toast.makeText(this,"No browser could open this link.",Toast.LENGTH_LONG).show();}
    }
    private void loadGame(String origin) {
        activeOrigin = origin;
        if(web != null) {web.removeAllViews(); web.destroy();}
        web = new WebView(this); web.setBackgroundColor(0xFF14281E);
        WebSettings s=web.getSettings(); s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setAllowFileAccess(false); s.setAllowContentAccess(false); s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW); s.setMediaPlaybackRequiresUserGesture(true); s.setSupportMultipleWindows(false);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web,false);
        WebView.setWebContentsDebuggingEnabled(false);
        WebViewAssetLoader.AssetsPathHandler assets = new WebViewAssetLoader.AssetsPathHandler(this);
        WebViewAssetLoader loader = new WebViewAssetLoader.Builder().addPathHandler("/", path -> {
            if(path.equals("api/config")) return new WebResourceResponse("application/json","UTF-8",new ByteArrayInputStream("{\"server\":false}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            WebResourceResponse r=assets.handle("game/"+(path.isEmpty()?"index.html":path));
            if(r==null) return new WebResourceResponse("text/plain","UTF-8",404,"Not Found",java.util.Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));
            return r;
        }).build();
        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest r) {return OFFLINE.equals(activeOrigin)?loader.shouldInterceptRequest(r.getUrl()):null;}
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {if(!r.isForMainFrame())return false;if(trusted(r.getUrl()))return false;external(r.getUrl().toString());return true;}
            @Override public void onReceivedError(WebView v, WebResourceRequest r, WebResourceError e) {if(r.isForMainFrame()) new AlertDialog.Builder(MainActivity.this).setTitle("Kingdom unavailable").setMessage("Check the server address and internet connection. Your server village is still saved.").setPositiveButton("Server & app",(d,w)->showChooser()).setNegativeButton("Retry",(d,w)->web.reload()).show();}
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public void onPermissionRequest(PermissionRequest request) {request.deny();}
        });
        if(WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            WebViewCompat.addWebMessageListener(web,"EmberfallHost",java.util.Collections.singleton(origin),(view,message,source,isMainFrame,reply)-> {
                if(!isMainFrame || !trusted(source))return;
                try {JSONObject d=new JSONObject(message.getData()); if("openExternal".equals(d.optString("action")))external(d.optString("url"));else if("chooseServer".equals(d.optString("action")))showChooser();} catch(Exception ignored) {}
            }); messageBridge=true;
        } else {Toast.makeText(this,"Update Android System WebView to enable app account sign-in.",Toast.LENGTH_LONG).show();}
        setContentView(web); web.onResume(); web.loadUrl(origin+"/");
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY|View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }
    @Override public void onBackPressed() {if(web!=null && web.getParent()!=null)showChooser();else super.onBackPressed();}
    @Override protected void onPause(){if(web!=null)web.onPause();CookieManager.getInstance().flush();super.onPause();}
    @Override protected void onResume(){super.onResume();if(web!=null && web.getParent()!=null)web.onResume();}
    @Override protected void onDestroy(){if(web!=null)web.destroy();super.onDestroy();}
}
