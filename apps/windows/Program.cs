using System.Diagnostics;
using System.Text.Json;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace Emberfall;
internal static class Program {
    [STAThread] static void Main() { ApplicationConfiguration.Initialize(); Application.Run(new KingdomWindow()); }
}
internal sealed class KingdomWindow : Form {
    const string Offline = "https://appassets.emberfall.local";
    readonly string profile = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Emberfall");
    readonly Color ink = Color.FromArgb(16,29,26), gold = Color.FromArgb(245,207,140);
    WebView2? web;
    string origin = Offline;
    public KingdomWindow() {
        Text="Emberfall · Kingdoms at War"; MinimumSize=new Size(820,480); Size=new Size(1280,800); StartPosition=FormStartPosition.CenterScreen; BackColor=ink; ForeColor=Color.WhiteSmoke; Font=new Font("Segoe UI",11);
        Directory.CreateDirectory(profile); ShowChooser();
    }
    static string? SecureOrigin(string value) {
        if(!Uri.TryCreate(value.Trim(),UriKind.Absolute,out var u) || u.Scheme!=Uri.UriSchemeHttps || u.UserInfo.Length>0 || u.AbsolutePath!="/" || u.Query.Length>0 || u.Fragment.Length>0) return null;
        return u.GetLeftPart(UriPartial.Authority);
    }
    bool Trusted(string value) => Uri.TryCreate(value,UriKind.Absolute,out var u) && u.GetLeftPart(UriPartial.Authority)==origin;
    static void External(string value) {
        if(!Uri.TryCreate(value,UriKind.Absolute,out var u) || u.Scheme!="https" || u.UserInfo.Length>0) return;
        try {Process.Start(new ProcessStartInfo(u.AbsoluteUri){UseShellExecute=true});} catch {MessageBox.Show("Open your system browser to continue.","Browser unavailable");}
    }
    Label Label(string text,int size,Color color) => new(){Text=text,AutoSize=true,Font=new Font("Segoe UI",size,size>22?FontStyle.Bold:FontStyle.Regular),ForeColor=color,Margin=new Padding(0,0,0,18),MaximumSize=new Size(780,0)};
    Button Button(string text,Action action) {var b=new Button(){Text=text,AutoSize=true,Padding=new Padding(18,11,18,11),BackColor=Color.FromArgb(38,67,49),ForeColor=gold,FlatStyle=FlatStyle.Flat,Margin=new Padding(0,8,16,8)};b.Click+=(_,_)=>action();return b;}
    void ShowChooser() {
        if(web!=null){web.Dispose();web=null;} Controls.Clear(); FormBorderStyle=FormBorderStyle.Sizable;
        var panel=new FlowLayoutPanel(){Dock=DockStyle.Fill,FlowDirection=FlowDirection.TopDown,WrapContents=false,AutoScroll=true,Padding=new Padding(48,36,48,28),BackColor=ink};
        panel.Controls.Add(Label("EMBERFALL",34,gold)); panel.Controls.Add(Label("Your kingdom, everywhere",21,Color.WhiteSmoke));panel.Controls.Add(Label("Play on this device or connect to your kingdom server.",13,Color.Silver));
        var input=new TextBox(){Width=650,Font=new Font("Segoe UI",15),PlaceholderText="https://your-kingdom.example",BackColor=Color.FromArgb(27,48,37),ForeColor=Color.WhiteSmoke,BorderStyle=BorderStyle.FixedSingle,Margin=new Padding(0,7,0,16)};
        try {input.Text=File.ReadAllText(Path.Combine(profile,"server.txt"));}catch(IOException){}
        panel.Controls.Add(input);var actions=new FlowLayoutPanel(){AutoSize=true,FlowDirection=FlowDirection.LeftToRight};
        actions.Controls.Add(Button("Connect to server",()=>{var address=SecureOrigin(input.Text);if(address==null||address==Offline){MessageBox.Show("Enter your HTTPS server address without a path.","Server address");return;}File.WriteAllText(Path.Combine(profile,"server.txt"),address);_=LoadGame(address);}));
        actions.Controls.Add(Button("Play on this device",()=>_=LoadGame(Offline)));panel.Controls.Add(actions);
        panel.Controls.Add(Label("Device play stays in this app. Server accounts and purchases require a connected server.\nVersion 5.0.0 · Use the game fullscreen button",12,Color.DarkSeaGreen));Controls.Add(panel);
    }
    async Task LoadGame(string address) {
        origin=address; Controls.Clear(); web=new WebView2(){Dock=DockStyle.Fill,DefaultBackgroundColor=ink};Controls.Add(web);
        try {
            var env=await CoreWebView2Environment.CreateAsync(null,Path.Combine(profile,"WebView"));await web.EnsureCoreWebView2Async(env);
            var core=web.CoreWebView2;core.Settings.AreDevToolsEnabled=false;core.Settings.AreDefaultContextMenusEnabled=false;core.Settings.AreBrowserAcceleratorKeysEnabled=false;core.Settings.IsPasswordAutosaveEnabled=false;core.Settings.IsGeneralAutofillEnabled=false;core.Settings.AreHostObjectsAllowed=false;
            core.SetVirtualHostNameToFolderMapping("appassets.emberfall.local",Path.Combine(AppContext.BaseDirectory,"Game"),CoreWebView2HostResourceAccessKind.DenyCors);
            core.NavigationStarting+=(_,e)=>{if(!Trusted(e.Uri)){e.Cancel=true;External(e.Uri);}};
            core.NewWindowRequested+=(_,e)=>{e.Handled=true;External(e.Uri);};
            core.PermissionRequested+=(_,e)=>e.State=CoreWebView2PermissionState.Deny;
            core.ServerCertificateErrorDetected+=(_,e)=>e.Action=CoreWebView2ServerCertificateErrorAction.Cancel;
            core.WebMessageReceived+=(_,e)=>{
                if(!Trusted(e.Source))return;
                try {using var doc=JsonDocument.Parse(e.WebMessageAsJson);var root=doc.RootElement;var action=root.GetProperty("action").GetString();if(action=="chooseServer")BeginInvoke((Action)ShowChooser);else if(action=="openExternal")External(root.GetProperty("url").GetString()??"");}catch(JsonException){}catch(KeyNotFoundException){}
            };
            core.ContainsFullScreenElementChanged+=(_,_)=>{FormBorderStyle=core.ContainsFullScreenElement?FormBorderStyle.None:FormBorderStyle.Sizable;if(core.ContainsFullScreenElement)WindowState=FormWindowState.Maximized;};
            core.NavigationCompleted+=(_,e)=>{if(!e.IsSuccess){MessageBox.Show("The kingdom could not load. Check the server address and internet connection.","Kingdom unavailable");ShowChooser();}};
            web.Source=new Uri(origin+"/");
        } catch(WebView2RuntimeNotFoundException) {
            if(MessageBox.Show("Install Microsoft's WebView2 Runtime to play Emberfall. Open its official download page?","WebView2 required",MessageBoxButtons.YesNo)==DialogResult.Yes) External("https://developer.microsoft.com/en-us/microsoft-edge/webview2/");ShowChooser();
        } catch(Exception) {MessageBox.Show("The game could not start. Close other Emberfall windows and try again.","Emberfall");ShowChooser();}
    }
    protected override void Dispose(bool disposing){if(disposing)web?.Dispose();base.Dispose(disposing);}
}
