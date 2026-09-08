# Emberfall 5 · Accounts and apps

The original 3D game, server-authoritative multiplayer economy, Town Hall hero gates, wall upgrades, clans, battles, Builder Base, Capital and season features are included. Version 5 adds high-resolution rendering profiles, six original hero portraits, a redesigned landscape interface, Google/Facebook accounts, and Android/iOS/Windows app projects. These apps contain the actual game assets and can play on the device immediately. Their online mode loads your HTTPS game server.

## Google and Facebook sign-in

Set these only in the server's private `.env`. Never put client secrets in the app project, public GitHub repository, or `dist/`.

```ini
PUBLIC_URL=https://YOUR_GAME_DOMAIN
COOKIE_SECURE=true
NODE_ENV=production
GOOGLE_CLIENT_ID=YOUR_WEB_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_WEB_CLIENT_SECRET
FACEBOOK_APP_ID=YOUR_META_APP_ID
FACEBOOK_APP_SECRET=YOUR_META_APP_SECRET
FACEBOOK_GRAPH_VERSION=v25.0
```

Use your actual origin, without a path or trailing slash. Configure these exact OAuth redirect URLs in the provider consoles:

| Provider | Client type | Authorized redirect URI |
| --- | --- | --- |
| Google | Web application | `https://YOUR_GAME_DOMAIN/api/auth/oauth/google/callback` |
| Facebook | Facebook Login for a website | `https://YOUR_GAME_DOMAIN/api/auth/oauth/facebook/callback` |

Google requests `openid profile`; Facebook requests `public_profile`. The game uses the verified provider subject ID and display name. It does not request email, friends, photos or publishing permissions. Configure your own provider consent screen, game domain and privacy policy, add test users while developing, and complete the provider's live/verification requirements before opening sign-in to the public. Restart the game server after setting keys. `/api/config` exposes only whether each provider is enabled, never its secret.

App sign-in opens the system browser. Complete Google/Facebook there, then return to the game. The original app or browser tab polls a short-lived, session-bound handoff to load the account. Provider tokens never enter the native bridge or browser storage. Callback state, Google nonce and PKCE, Google JWT signature/audience/issuer/expiry, Facebook app identity and `appsecret_proof` are checked on the server. Attempts expire in 10 minutes and cannot be claimed twice.

A first sign-in saves the current guest village. Signing into an existing account opens that account's existing village. Account → Connect links another provider to the current account. Accounts are never linked by a matching email and wallets are never merged. A linked provider that already belongs to another village is rejected. Existing password accounts still work. Social accounts can purchase gems when the separately configured payment provider is enabled.

The source and tests are ready; real provider sign-in requires your developer app IDs/secrets and HTTPS domain. Those private credentials were not supplied with this project.

## Android

Open `apps/android` in Android Studio. Install JDK 17+, Android SDK 36 and Gradle 8.13. At repository root run `node scripts/prepare-app-assets.mjs android`, then inside `apps/android` run:

```sh
gradle :app:assembleRelease :app:bundleRelease
```

CI compiles a non-debug, optimized release APK and AAB. Release outputs are unsigned until you sign them with your private Android key. To distribute an APK, use `apksigner sign` with your key and then `apksigner verify --verbose --print-certs`. Keep the same signing key for updates. A debug key must not be used as your release identity. Private signing material is excluded from source control.

Android 7+ with WebGL 2 and an up-to-date Android System WebView is required. The app locks to landscape where supported. Embedded file access, mixed content, third-party cookies and WebView debugging are disabled. The native bridge accepts only browser-opening and server-selection messages from the current top-level game origin. It cannot change gems, account state or combat results.

## iPhone and iPad

Run `node scripts/prepare-app-assets.mjs ios` and open `apps/ios/Emberfall.xcodeproj` on a Mac. Select your Apple signing team and unique bundle identifier, then run on your iPhone or archive for distribution. Deployment target is iOS 15. The project has a shared scheme and full icon set.

CI compiles both the iOS Simulator app and an **unsigned device IPA**. An unsigned IPA does not install on an ordinary iPhone. Installing on a physical device or distributing through TestFlight/App Store requires your Apple signing identity and provisioning profile. They were not supplied. This project is not an App Store approval or publication.

Offline assets are served only on `127.0.0.1:18731`, with no state or write endpoints. The embedded browser loads online games only from the HTTPS origin you selected. The bridge checks the message frame and origin.

## Windows

Run `node scripts/prepare-app-assets.mjs windows`, then:

```sh
dotnet publish apps/windows/Emberfall.csproj -c Release -r win-x64 --self-contained true -o release/windows
```

Copy the entire published folder and open `Emberfall.exe`. The app bundles .NET; Microsoft WebView2 Runtime must be installed. Its official download page opens if the runtime is missing. The build is not Authenticode signed; use your own code-signing certificate for public distribution. F11 toggles fullscreen. Settings → Server & app changes servers.

## GitHub and your server

GitHub stores the source and GitHub Actions builds/tests the game and native apps. Open Actions → **Build native apps** → a successful run to download the Android, Windows and iOS artifacts. Artifacts are retained for 30 days, so keep a separate copy of releases. See the main README for the existing VPS/container deployment workflows. GitHub Pages cannot run this persistent Node/SQLite game server.

The same game and server version should be deployed together. Back up the SQLite data directory before updating. This version creates new account tables automatically and preserves existing villages.

## မြန်မာလို အမြန်စတင်နည်း

1. Server source အဖြစ် ZIP ထဲက `emberfall` folder ကို သုံးပါ။ README ထဲက Docker/VPS အဆင့်တွေအတိုင်း တင်ပါ။
2. Google/Facebook login အစစ်သုံးဖို့ အပေါ်က key တွေကို server ရဲ့ `.env` ထဲမှာ ဖြည့်ပါ။ Key ကို GitHub ပေါ် မတင်ပါနဲ့။
3. App ကိုဖွင့်ပြီး **Play on this device** ကို နှိပ်ရင် device ထဲမှာ တန်းကစားနိုင်တယ်။ Online village သုံးဖို့ **Connect to server** မှာ ကိုယ့် game server ရဲ့ HTTPS လိပ်စာ ထည့်ပါ။
4. **Village account** ထဲက Google/Facebook ကို ရွေးပါ။ Browser မှာ အကောင့်ဝင်ပြီးရင် မူလ game app ထဲ ပြန်ဝင်ပါ။
5. **Settings → 3D graphics → Ultra HD** က အကြည်ဆုံး setting ဖြစ်တယ်။ ဖုန်းပူခြင်း၊ ဘက်ထရီကုန်မြန်ခြင်းရှိရင် High သို့မဟုတ် Smooth ကို သုံးပါ။
6. **Kingdom → Heroes** မှာ Hero ပုံ၊ level၊ Town Hall လိုအပ်ချက်နဲ့ upgrade ကို ကြည့်နိုင်တယ်။ ပုံတွေဟာ ဒီဂိမ်းအတွက် ဖန်တီးထားတဲ့ ကိုယ်ပိုင်ပုံတွေ ဖြစ်တယ်။
7. iPhone app ကို သာမန် iPhone ထဲသွင်းဖို့ Apple signing လိုတယ်။ Unsigned IPA ကို install လုပ်ပြီးသား app လို့ မယူဆပါနဲ့။

## Implementation references

- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)
- [Google web server OAuth](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Facebook manual login flow](https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow/)
- [Android WebKit](https://developer.android.com/jetpack/androidx/releases/webkit)
- [Android Gradle 8.13 compatibility](https://developer.android.com/build/releases/agp-8-13-0-release-notes)
- [Microsoft WebView2 SDK releases](https://learn.microsoft.com/en-us/microsoft-edge/webview2/release-notes/sdk/)
