import SwiftUI

@main
struct EmberfallApp: App {
    var body: some Scene { WindowGroup { KingdomView().preferredColorScheme(.dark) } }
}
struct KingdomView: View {
    @AppStorage("kingdomServer") private var savedServer = ""
    @State private var address = ""
    @State private var target: URL?
    @State private var error = ""
    @StateObject private var assets = AssetServer()
    private let gold = Color(red:0.96,green:0.82,blue:0.55)
    var body: some View {
        ZStack {
            Color(red:0.063,green:0.114,blue:0.102).ignoresSafeArea()
            if let url = target {
                KingdomWebView(url:url,chooseServer:{target=nil},failed:{error=$0;target=nil}).ignoresSafeArea().statusBarHidden()
            } else {
                ScrollView {
                    VStack(alignment:.leading,spacing:18) {
                        Text("EMBERFALL").font(.system(size:34,weight:.bold,design:.serif)).foregroundColor(gold)
                        Text("Your kingdom, everywhere").font(.title2)
                        Text("Play on this device or connect to your kingdom server.").foregroundColor(.secondary)
                        TextField("https://your-kingdom.example",text:$address).textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL).padding(14).background(Color.white.opacity(0.07)).cornerRadius(10)
                        HStack(spacing:16) {
                            Button("Connect to server") {
                                guard let u=URL(string:address.trimmingCharacters(in:.whitespacesAndNewlines)),u.scheme=="https",u.host != nil,u.user==nil,u.password==nil,u.query==nil,u.fragment==nil,u.path.isEmpty || u.path=="/" else {error="Enter your HTTPS server address without a path.";return}
                                savedServer=u.absoluteString;error="";target=u
                            }.buttonStyle(.borderedProminent).tint(gold).foregroundColor(.black)
                            Button("Play on this device") {Task {do {try await assets.start(); error=""; target=assets.url} catch {self.error="Device play could not start. Close other Emberfall instances and try again."}}}.buttonStyle(.bordered).tint(gold)
                        }.controlSize(.large)
                        if !error.isEmpty {Text(error).foregroundColor(.orange)}
                        Text("Device play stays in this app. Server accounts and purchases require a connected server. Version 5.0.0").font(.footnote).foregroundColor(.secondary)
                    }.padding(30).frame(maxWidth:800)
                }
            }
        }.onAppear {address=savedServer; UIApplication.shared.isIdleTimerDisabled=true}
    }
}
