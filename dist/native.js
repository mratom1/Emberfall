export function nativeApp() { return !!(window.EmberfallHost || window.EmberfallAndroid || window.webkit?.messageHandlers?.emberfall || window.chrome?.webview); }
export function openExternal(value, popup) {
  const u = new URL(value); if (u.protocol !== 'https:' || u.username || u.password) throw new Error('A secure HTTPS link is required.');
  if (window.EmberfallHost) window.EmberfallHost.postMessage(JSON.stringify({action:'openExternal',url:u.href}));
  else if (window.EmberfallAndroid) window.EmberfallAndroid.openExternal(u.href);
  else if (window.webkit?.messageHandlers?.emberfall) window.webkit.messageHandlers.emberfall.postMessage({action: 'openExternal', url: u.href});
  else if (window.chrome?.webview) window.chrome.webview.postMessage({action: 'openExternal', url: u.href});
  else if (popup && !popup.closed) popup.location.replace(u.href);
  else window.open(u.href, '_blank', 'noopener,noreferrer');
}
export function chooseServer() {
  if (window.EmberfallHost) window.EmberfallHost.postMessage(JSON.stringify({action:'chooseServer'}));
  else if (window.EmberfallAndroid) window.EmberfallAndroid.chooseServer();
  else if (window.webkit?.messageHandlers?.emberfall) window.webkit.messageHandlers.emberfall.postMessage({action:'chooseServer'});
  else window.chrome?.webview?.postMessage({action:'chooseServer'});
}
