import SwiftUI
import WebKit
struct KingdomWebView: UIViewRepresentable {
    let url: URL
    var chooseServer: ()->Void
    var failed: (String)->Void
    func makeCoordinator()->Coordinator {Coordinator(self)}
    func makeUIView(context: Context)->WKWebView {
        let config=WKWebViewConfiguration(); config.websiteDataStore = .default()
        config.userContentController.add(context.coordinator,name:"emberfall")
        let view=WKWebView(frame:.zero,configuration:config); view.isOpaque=false;view.backgroundColor = .black;view.scrollView.isScrollEnabled=false;view.navigationDelegate=context.coordinator;view.uiDelegate=context.coordinator;view.allowsBackForwardNavigationGestures=false
        if #available(iOS 16.4,*) {view.isInspectable=false}
        view.load(URLRequest(url:url));return view
    }
    func updateUIView(_ view: WKWebView,context: Context) {}
    static func dismantleUIView(_ view: WKWebView,coordinator: Coordinator) {view.stopLoading();view.configuration.userContentController.removeScriptMessageHandler(forName:"emberfall");view.navigationDelegate=nil;view.uiDelegate=nil}
    class Coordinator: NSObject,WKNavigationDelegate,WKUIDelegate,WKScriptMessageHandler {
        let parent: KingdomWebView
        init(_ parent: KingdomWebView){self.parent=parent}
        func trusted(_ u:URL)->Bool {u.scheme==parent.url.scheme && u.host==parent.url.host && u.port==parent.url.port}
        func external(_ u:URL) {guard u.scheme=="https",u.user==nil,u.password==nil else{return};UIApplication.shared.open(u)}
        func userContentController(_ userContentController: WKUserContentController,didReceive message: WKScriptMessage) {
            guard message.frameInfo.isMainFrame,let u=message.frameInfo.request.url,trusted(u),let d=message.body as? [String:Any],let action=d["action"] as? String else{return}
            if action=="chooseServer" {parent.chooseServer()} else if action=="openExternal",let value=d["url"] as? String,let target=URL(string:value) {external(target)}
        }
        func webView(_ webView: WKWebView,decidePolicyFor action: WKNavigationAction,decisionHandler: @escaping (WKNavigationActionPolicy)->Void) {
            guard let u=action.request.url else{decisionHandler(.cancel);return}
            if action.targetFrame?.isMainFrame == false {decisionHandler(.allow);return}
            if trusted(u) {decisionHandler(.allow)} else {external(u);decisionHandler(.cancel)}
        }
        func webView(_ webView:WKWebView,createWebViewWith configuration:WKWebViewConfiguration,for action:WKNavigationAction,windowFeatures:WKWindowFeatures)->WKWebView? {if let u=action.request.url {external(u)};return nil}
        func webView(_ webView:WKWebView,didFailProvisionalNavigation navigation:WKNavigation!,withError error:Error) {if (error as NSError).code != NSURLErrorCancelled {parent.failed("Kingdom unavailable. Check the server address and your connection.")}}
        func webViewWebContentProcessDidTerminate(_ webView:WKWebView) {parent.failed("Graphics paused. Reopen your kingdom, or choose Smooth graphics on this device.")}
    }
}
