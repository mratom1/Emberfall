# Emberfall v4 — Server ပေါ်တင်နည်း

ဒီ ZIP ထဲမှာ frontend၊ backend၊ ဂိမ်းပုံစံတွေ၊ database စတင်ပေးတဲ့ code၊ Docker ဖိုင်နဲ့ စမ်းသပ်ချက်တွေ ပါပါတယ်။ ဆော့ဖို့ payment key မလိုပါဘူး။ Gem ကို ငွေနဲ့ရောင်းချင်မှ payment ချိတ်ရပါမယ်။

GitHub ကနေ server ဆီတင်နည်းကို **GITHUB_DEPLOY_MM.md** မှာ အဆင့်လိုက်ထည့်ထားပါတယ်။ Feature အသစ်တွေအတွက် **CHANGELOG.md** ကိုကြည့်ပါ။

## ၁။ ဖိုင်ဖြည်ပါ

```sh
unzip Emberfall_Full_Source_v4.zip
cd emberfall
```

Server mode အတွက် folder အကုန်တင်ပါ။ dist folder တစ်ခုတည်းတင်ရင် account၊ Clan၊ player raid နဲ့ payment မရပါဘူး။

## ၂။ စတင်ပါ — နည်းလမ်းတစ်ခုရွေးပါ

**Node.js 24 ရှိပြီးသားဆို**

```sh
node --version
npm start
```

v24 သို့မဟုတ် အထက်ဖြစ်ရပါမယ်။ npm install မလိုပါဘူး။ Browser မှာ `http://SERVER_IP:8080` ကိုဖွင့်ပါ။ SERVER_IP နေရာမှာ ကိုယ့် server IP အစစ်ထည့်ပါ။ Firewall မှာ port 8080 ကို ခွင့်ပြုထားဖို့လိုပါတယ်။

ဒီနည်းက terminal ပိတ်ရင် process ရပ်နိုင်လို့ အမြဲတမ်းတင်ထားဖို့ Docker နည်းကို သုံးနိုင်ပါတယ်။ deploy/emberfall.service ကို ကိုယ့် path/user အတိုင်းပြင်ပြီး systemd service အဖြစ်လည်း သုံးနိုင်ပါတယ်။

**Docker + Compose ရှိပြီးသားဆို**

```sh
sh start.sh
```

.env မရှိသေးရင် တစ်ခါတည်းဖန်တီးပြီး background မှာစတင်ပေးမယ်။ Server ပြန်တက်လာရင် container ပြန်စမယ်။ ပထမအကြိမ်မှာ Docker image ဒေါင်းဖို့ internet လိုပါတယ်။

`http://SERVER_IP:8080` မှာဆော့ပါ။ Port 8080 ကို တခြား app သုံးနေရင် .env ထဲက PORT ကို 8081 လိုပြောင်းပြီး ပြန်စပါ။

## ၃။ Domain နဲ့ HTTPS

Domain DNS ကို server IP ဆီချိတ်ပါ။ .env ထဲမှာ:

```dotenv
DOMAIN=game.your-domain.com
```

ပြီးရင်:

```sh
docker compose -f compose.https.yml up -d --build
```

Caddy က HTTPS certificate နဲ့ reverse proxy ကို ပြင်ဆင်ပေးမယ်။ Port 80/443 ကို ခွင့်ပြုထားရပါမယ်။ အဲဒီ port တွေမှာ Nginx/Caddy တစ်ခုရှိပြီးသားဆို ထပ်မစပါနဲ့။ ရှိပြီးသား HTTPS reverse proxy ကနေ 127.0.0.1:8080 ကိုချိတ်ပါ။ deploy/nginx.conf.example မှာနမူနာရှိပါတယ်။

ရှိပြီးသား HTTPS proxy နဲ့ standard compose.yml ကိုသုံးမယ်ဆို .env မှာ:

```dotenv
BIND_ADDRESS=127.0.0.1
PUBLIC_URL=https://game.your-domain.com
COOKIE_SECURE=true
NODE_ENV=production
```

ပြီးရင် `docker compose up -d --build` ပြန်လုပ်ပါ။ Account password နဲ့ ငွေပေးချေမှုအတွက် HTTPS သုံးပါ။

## ၄။ Account နဲ့ ရွာသိမ်းပုံ

- စဖွင့်တာနဲ့ guest ရွာတစ်ရွာရပြီး server database ထဲသိမ်းပေးမယ်။
- HTTPS domain နဲ့ဖွင့်ပြီး Settings → Village account မှာ username/password သတ်မှတ်ပါ။ Public HTTP မှာ account ဝင်ခွင့်ပိတ်ထားပြီး guest အဖြစ်တော့ ဆော့နိုင်ပါတယ်။
- တခြားစက်မှာ အဲဒီ account နဲ့ပြန်ဝင်ရင် ရွာဟောင်းကို ဆက်ဆော့နိုင်ပါတယ်။
- Standalone browser ထဲက ရွာကို server account ထဲ အလိုအလျောက်မတင်ပါဘူး။
- Email နဲ့ password ပြန်ယူစနစ် မပါသေးလို့ password ကိုမှတ်ထားပါ။
- Node နဲ့စရင် data/emberfall.sqlite၊ Docker နဲ့စရင် persistent volume ထဲသိမ်းပါတယ်။

## ၅။ Gem ဆိုင်

Gem pack၊ ဝယ်မယ့်ခလုတ်နဲ့ Stripe Checkout backend ပါပြီးသားပါ။ Key မထည့်သေးရင် ဝယ်ခလုတ်ပိတ်ထားမယ်။ သစ်ပင်ခုတ်လို့ရတဲ့ Gem နဲ့ ကျန်တဲ့စနစ်တွေက ဆက်အလုပ်လုပ်ပါတယ်။

.env ထဲမှာ ကိုယ့် STRIPE_SECRET_KEY နဲ့ STRIPE_WEBHOOK_SECRET ထည့်ပါ။ Key ကို frontend ဖိုင်ထဲမထည့်ပါနဲ့။ ပထမဆုံး test key နဲ့စမ်းပါ။

Webhook URL:

```text
https://game.your-domain.com/api/payments/webhook
```

Stripe မှာ checkout.session.completed နဲ့ checkout.session.async_payment_succeeded ကို ဖွင့်ပါ။ Game ကို restart လုပ်ပါ။ အသေးစိတ် PAYMENTS.md မှာဖတ်ပါ။ အခြား payment ဝန်ဆောင်မှုသုံးမယ်ဆို server/payments.mjs နဲ့ payment endpoint တွေကို ပြောင်းရပါမယ်။

## ၆။ ဆော့ပုံ

1. ဖုန်းကိုဘေးတိုက်လှည့်ပြီး Auto-rotate ဖွင့်ပါ။ Fullscreen ခလုတ်က browser ခွင့်ပြုတဲ့စက်မှာ orientation lock လုပ်ပေးမယ်။
2. Build → အဆောက်အဦးရွေး → 3D preview ကိုရွှေ့ → အစိမ်းရောင်နေရာမှာ **Build here** ကိုနှိပ်ပါ။ Rotate ခလုတ်နဲ့လှည့်နိုင်ပါတယ်။
3. အဆောက်အဦးပေါ်နှိပ်ပြီး Upgrade / Move လုပ်ပါ။
4. သစ်ပင်/ကျောက်တုံးကို Clear လုပ်ပါ။ 42% အခွင့်အရေးနဲ့ Gem 1–6 ခု ရနိုင်ပါတယ်။ မရတဲ့အကြိမ်လည်းရှိပါတယ်။
5. Town Hall တိုးရင် အဆောက်အဦးအသစ်တွေဖွင့်မယ်။ Barracks တိုးရင် စစ်သားအသစ်ဖွင့်မယ်။ Laboratory မှာ စစ်သားအင်အားတိုးပါ။
6. Hero Hall မှာ Hero ငါးကောင်ကို ဖွင့်/တိုးနိုင်ပါတယ်။ တိုက်ပွဲမှာ Hero ချပြီး Ability တစ်ကြိမ်သုံးနိုင်ပါတယ်။
7. Spell Forge မှာ မိုးကြိုး၊ သွေးဖြည့်၊ Rage နဲ့ Freeze ထုတ်ပါ။
8. Battle → Scout → အနီရောင်ဘောင်အပြင်မှာ စစ်သားချပါ။
9. Clans & Rivals မှာ Clan ဖွဲ့၊ ချိတ်၊ စာပို့၊ Guardian လှူနိုင်ပါတယ်။ Server ပေါ်မှာ ကစားသမားနှစ်ယောက်နှင့်အထက်ရှိမှ တခြားသူ့ရွာကိုတိုက်နိုင်ပါတယ်။

## ၇။ Backup / Update

```sh
docker compose exec game node scripts/backup.mjs
docker compose cp game:/app/data/backups ./backups
```

HTTPS Compose သုံးရင် command တိုင်းမှာ `docker compose -f compose.https.yml` သုံးပါ။

Code အသစ်တင်ပြီး data မပျက်ဘဲ ပြန်စရန်:

```sh
docker compose up -d --build
```

`docker compose down -v` က player data volume ကိုဖျက်နိုင်လို့ data ဖျက်ချင်တဲ့အခါမှသုံးပါ။

## ၈။ Hero နဲ့ Town Hall ချိတ်ဆက်မှု

| Hero | ဖွင့်နိုင်မယ့် Town Hall |
|---|---:|
| Ember King | 2 |
| Moon Ranger | 3 |
| Dusk Prince | 4 |
| Storm Warden | 5 |
| Dawn Champion | 7 |

Hero Hall ဆောက်ပြီး dark elixir နဲ့ဖွင့်ရပါတယ်။ စဖွင့်တဲ့ TH အဆင့်မှာ Hero level 5 အထိတင်နိုင်ပြီး TH တစ်ဆင့်တက်တိုင်း cap 5 တိုးပါတယ်။ Hero menu မှာ လက်ရှိ cap ကိုပြပါတယ်။ Equipment နှစ်ခုနဲ့ pet တစ်ကောင် တပ်နိုင်ပါတယ်။ Training grounds က ယာယီစမ်းသုံးဖို့ဖြစ်ပြီး Hero ကို အခမဲ့ဖွင့်ပေးတာ မဟုတ်ပါဘူး။

## ၉။ အသစ်ထည့်ထားတဲ့စနစ်များ

- **Worlds → Builder Base**: သီးခြားရွာ၊ gold/elixir၊ စစ်သား၊ အဆောက်အဦး level 10 အထိ၊ Battle Machine နဲ့ တိုက်ပွဲ ပါပါတယ်။ Home village ခလုတ်နဲ့ ပြန်နိုင်ပါတယ်။
- **Heroes → Equipment / Pets / Siege**: Equipment ရှစ်မျိုး၊ pet လေးကောင်၊ siege machine သုံးမျိုး ထုတ်/တိုး/တပ်နိုင်ပါတယ်။ Pet က Hero ချတဲ့အခါ လိုက်ဆင်းပြီး တိုက်ခိုက် သို့မဟုတ် သွေးဖြည့်ပေးပါတယ်။
- **Clan Wars**: တကယ့် clan နှစ်ဖွဲ့ အင်အားအရေအတွက်တူတူ 1v1 မှ 5v5 အထိ။ Leader ကစပြီး တစ်မိနစ်ပြင်ဆင်ချိန်၊ 24 နာရီတိုက်ချိန် ပါပါတယ်။ တစ်ယောက်ကို အများဆုံးနှစ်ကြိမ်၊ target တစ်ခုကိုတစ်ကြိမ် တိုက်နိုင်ပါတယ်။ 1v1 မှာ တစ်ကြိမ်စီပါ။
- **Clan Capital**: Clan အတူသုံးတဲ့ 3D ရွာကို လှူထားတဲ့ capital gold နဲ့ leader က ဆောက်/တိုး/ရွှေ့နိုင်ပါတယ်။ ရန်သူ့ district သုံးခုကို ဆက်တိုက်နိုင်ပြီး ပျက်စီးမှုဆက်သိမ်းပါတယ်။ တစ်ပတ်ကို တစ်ယောက်ငါးကြိမ် တိုက်နိုင်ပါတယ်။
- **Clan League**: AI stronghold တွေကို ခုနစ်ပွဲစီးရီးတိုက်တဲ့ clan league ပါ။ Clan Wars က player clan အချင်းချင်းဖြစ်ပြီး League က AI ပြိုင်ဘက်ဖြစ်ကြောင်း menu မှာဖော်ပြထားပါတယ်။
- **Season**: နေ့စဉ် challenge၊ အခမဲ့ season pass tier 20၊ gems/ore/capital gold ဆုနဲ့ medal ဆိုင် ပါပါတယ်။ UTC လအစမှာ season အသစ်စပါတယ်။

တိုက်ပွဲဝင်ဖို့ Scout/Attack ကိုနှိပ်တာနဲ့ war/capital/league attempt ကို သုံးပြီးသားဖြစ်ပါတယ်။ မတိုက်ဘဲပြန်ထွက်ရင် attempt ပြန်မရပါဘူး။

## ၁၀။ လုံခြုံရေး

အများပြည်သူဆော့မယ့် server မှာ folder အကုန်နဲ့ Node backend ကိုသုံးပါ။ dist တစ်ခုတည်းတင်တဲ့ offline mode က browser save ကိုကိုယ်တိုင်ပြင်နိုင်လို့ online ပိုက်ဆံ/ဆုစနစ်အတွက် မသုံးရပါဘူး။

Server က Gem/ငွေ/level/အချိန်/တိုက်ပွဲရလဒ်ကို ဆုံးဖြတ်ပါတယ်။ Browser က balance အတု၊ Hero level အတု၊ ဆုအတု ပို့တာကို လက်မခံပါဘူး။ Payment အစစ် အတည်ပြုချက်မရဘဲ Gem မတိုးပါဘူး။

Account အသုံးပြုဖို့ HTTPS လိုပါတယ်။ Password ပြောင်းရင် တခြားစက် session တွေ အကုန်ပြုတ်ပါမယ်။ Docker က game process ကို root မဟုတ်တဲ့ user နဲ့စပြီး source folder ကို read-only ထားပါတယ်။ Secret key တွေနဲ့ database က public URL ကနေ မဖတ်နိုင်ပါဘူး။

လုံးဝ hack မခံရဘူးလို့ အာမခံနိုင်တဲ့ software မရှိပါဘူး။ ဒီစမ်းသပ်ချက်တွေကလည်း external penetration test မဟုတ်ပါဘူး။ VPS/OS/Docker update နဲ့ HTTPS၊ firewall၊ backup ကို ဆက်ထိန်းသိမ်းပါ။ အသေးစိတ် SECURITY.md မှာပါပါတယ်။

## v4 မှာ ထပ်ပါလာတာ

- Wall တစ်ခုချင်း/အစုလိုက် upgrade၊ map ပေါ်ရွေးချယ်မှု၊ စုစုပေါင်းစျေးနဲ့ level အလိုက် 3D ပုံစံပြောင်းမှု။ Town Hall 4 ရောက်ရင် Gold အစား Elixir နဲ့လည်းမြှင့်နိုင်ပါတယ်။
- Army ထဲက Army presets မှာ ရွာတစ်ရွာကို စစ်တပ်ပုံစံ 3 ခုသိမ်းပြီး လိုတဲ့ troop ကိုတစ်ချက်နဲ့ပြန်လေ့ကျင့်နိုင်ပါတယ်။
- Work queue မှာ ရွာနှစ်ရွာက ဆောက်လုပ်ရေး၊ Hero/research/training တို့ကို တစ်နေရာမှာကြည့်နိုင်ပါတယ်။
- လိုင်းပြတ်ပြီး ပြန်ပို့တဲ့ command ကို ငွေနှစ်ခါမနုတ်ပါဘူး။ အတည်မပြုရသေးရင် Retry connection နဲ့ပြန်ချိတ်ပါ။
- Server က 6 နာရီတစ်ကြိမ် backup အလိုအလျောက်ယူပြီး automatic copy 28 ခုထားပါတယ်။ Backup ကို တခြားနေရာဆီ ထပ်ကူးထားဖို့လိုပါတယ်။

## စမ်းသပ်ပြီးမှု

Gameplay 13 ခု၊ core server 9 ခု၊ expansion 11 ခု၊ security 11 ခု၊ quality/recovery 12 ခု၊ deployment failure simulation 4 ခု — စုစုပေါင်း **60 ခု** အောင်မြင်ထားပါတယ်။ Node server ကိုစပြီး API တွေကိုတကယ်စမ်းထားပါတယ်။ Browser ပုံရိပ်စစ်ခြင်း၊ Docker image build၊ public HTTPS certificate နဲ့ payment အစစ်ကို ဒီပတ်ဝန်းကျင်မှာ မစမ်းထားပါဘူး။

မူရင်း COC ရဲ့ code/art သို့မဟုတ် content အားလုံးကို တစ်ထပ်တည်းကူးထားတာ မဟုတ်ပါဘူး။ Emberfall ရဲ့ကိုယ်ပိုင် rule၊ balance၊ level နဲ့ အပေါ်ကဖော်ပြထားတဲ့ playable systems တွေဖြစ်ပါတယ်။
