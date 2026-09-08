import Foundation
import Network
import Combine

// Loopback, public bundled assets only. No game state, credentials or write API.
final class AssetServer: ObservableObject {
    private var listener:NWListener?
    private let queue=DispatchQueue(label:"game.emberfall.assets")
    let url=URL(string:"http://127.0.0.1:18731/")!
    func start() async throws {
        if listener != nil {return}
        let parameters=NWParameters.tcp
        parameters.requiredLocalEndpoint = .hostPort(host:"127.0.0.1",port:18731)
        let l=try NWListener(using:parameters); listener=l
        l.newConnectionHandler={ [weak self] c in guard let self=self else{c.cancel();return};c.start(queue:self.queue);self.receive(c,Data()) }
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            var finished=false
            l.stateUpdateHandler={ [weak self] state in
                switch state {
                case .ready: if !finished {finished=true;continuation.resume()}
                case .failed(let error): self?.listener=nil;if !finished {finished=true;continuation.resume(throwing:error)}
                default: break
                }
            }
            l.start(queue:queue)
        }
    }
    private func receive(_ c:NWConnection,_ previous:Data) {
        c.receive(minimumIncompleteLength:1,maximumLength:8192) { [weak self] data,_,complete,error in
            guard let self=self,error==nil else{c.cancel();return}
            var all=previous;if let data=data {all.append(data)}
            guard all.count<=8192 else{c.cancel();return}
            guard let text=String(data:all,encoding:.utf8),text.contains("\r\n\r\n") else{if complete {c.cancel()}else{self.receive(c,all)};return}
            let lines=text.components(separatedBy:"\r\n"),parts=(lines.first ?? "").split(separator:" ")
            guard parts.count==3,parts[0]=="GET",lines.contains(where:{$0.lowercased()=="host: 127.0.0.1:18731"}) else{self.send(c,403,"text/plain",Data());return}
            let raw=String(parts[1]).split(separator:"?",maxSplits:1).first.map(String.init) ?? "/"
            guard let decoded=raw.removingPercentEncoding,decoded.hasPrefix("/"),!decoded.contains("\0"),!decoded.split(separator:"/").contains(where:{$0.hasPrefix(".")}),let root=Bundle.main.resourceURL?.appendingPathComponent("Game",isDirectory:true) else{self.send(c,404,"text/plain",Data());return}
            if decoded=="/api/config" {self.send(c,200,"application/json",Data("{\"server\":false}".utf8));return}
            let path=decoded=="/" ? "index.html" : String(decoded.dropFirst())
            let file=root.appendingPathComponent(path).standardizedFileURL
            guard file.path.hasPrefix(root.path+"/"),let content=try? Data(contentsOf:file) else{self.send(c,404,"text/plain",Data());return}
            let mime=["html":"text/html","js":"text/javascript","css":"text/css","json":"application/json","webmanifest":"application/manifest+json","webp":"image/webp","png":"image/png","woff2":"font/woff2"]
            self.send(c,200,mime[file.pathExtension] ?? "application/octet-stream",content)
        }
        queue.asyncAfter(deadline:.now()+10) {c.cancel()}
    }
    private func send(_ c:NWConnection,_ status:Int,_ mime:String,_ data:Data) {
        var response=Data("HTTP/1.1 \(status) \(status==200 ? "OK" : "Unavailable")\r\nContent-Type: \(mime)\r\nContent-Length: \(data.count)\r\nConnection: close\r\nCache-Control: no-cache\r\nX-Content-Type-Options: nosniff\r\nContent-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'\r\n\r\n".utf8);response.append(data)
        c.send(content:response,completion:.contentProcessed{_ in c.cancel()})
    }
    deinit {listener?.cancel()}
}
