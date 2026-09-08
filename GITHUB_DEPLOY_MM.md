# GitHub မှ VPS ဆီတင်ခြင်း — Emberfall v4

GitHub က source code သိမ်းပြီး စမ်းသပ်၊ Docker image ထုတ်၊ ကိုယ့် VPS ဆီပို့ပေးနိုင်ပါတယ်။ **GitHub Pages မှာ Node backend နဲ့ SQLite database ကို run မရပါဘူး။** Full game ကို VPS မှာ run ရပါတယ်။ GitHub Actions runner ကိုလည်း အမြဲဖွင့်ထားတဲ့ game server အဖြစ် မသုံးပါနဲ့။

## ပထမတစ်ကြိမ် — repository

GitHub မှာ `emberfall-kingdoms` လိုနာမည်နဲ့ **Private repository** ဖန်တီးပြီး ဒီ project ထဲက source ဖိုင်အားလုံးတင်ပါ။ `.github` folder နဲ့ `.env.example` ပါရပါမယ်။ `.env` အစစ်၊ database၊ backup၊ SSH key နဲ့ `.openai` folder ကို မတင်ပါနဲ့။ ဒီ ZIP ထဲမှာ production secret မပါပါဘူး။

GitHub CLI ရှိပြီး login ဝင်ထားတဲ့ ကွန်ပျူတာမှာ ZIP ဖြည်ပြီး အောက်ပါအတိုင်းလည်း တင်နိုင်ပါတယ်။ လက်ရှိ repository ထဲမှာ မ run ဘဲ ZIP အသစ်ဖြည်ထားတဲ့ `emberfall` folder ထဲမှာ run ပါ။

```sh
git init -b main
git add .
git commit -m "Release Emberfall v4"
gh repo create emberfall-kingdoms --private --source=. --remote=origin --push
```

Repository တင်ပြီးတိုင်း `Verify game` က စမ်းသပ်ချက်တွေ၊ Docker build နဲ့ container smoke test ကို run မယ်။ Pull request တွေမှာ deployment secret မသုံးပါဘူး။

## ပထမတစ်ကြိမ် — VPS

Linux x86-64 VPS အတွက် Docker Engine + Compose v2၊ Python 3၊ OpenSSH နဲ့ `flock` ရှိရပါမယ်။ လက်ရှိ workflow က x86-64 Docker image ထုတ်ပါတယ်။ ARM server မှာသုံးဖို့ workflow ကို ARM/multi-architecture build အဖြစ်ပြင်ရပါမယ်။

ကိုယ့် VPS user နဲ့:

```sh
sudo install -d -m 0750 -o "$USER" -g "$(id -gn)" /opt/emberfall
```

Project ရဲ့ `.env.example` ကို `/opt/emberfall/.env` အဖြစ်ကူးပါ။ Permission ကို `chmod 600 /opt/emberfall/.env` လုပ်ပါ။ ပြီးရင်:

```dotenv
DOMAIN=game.your-domain.com
PORT=8080
COMPOSE_PROFILES=managed-tls
BACKUP_ENABLED=true
BACKUP_INTERVAL_HOURS=6
BACKUP_KEEP=28
```

`DOMAIN` ကို ကိုယ့် domain အစစ်နဲ့ အစားထိုးပြီး DNS ကို VPS ဆီချိတ်ပါ။ ပုံမှန်နည်းက Caddy နဲ့ HTTPS အလိုအလျောက်ရအောင်လုပ်ပေးတယ်။ Port 80/443 ကို အသုံးပြုမယ်။

**VPS မှာ Nginx/HTTPS ရှိပြီးသားဆို** `COMPOSE_PROFILES=` အလွတ်ထားပါ။ Caddy ကို မစဘဲ ရှိပြီးသား HTTPS proxy ကနေ `127.0.0.1:8080` ဆီချိတ်ပါ။ `deploy/nginx.conf.example` ကို ကိုယ့် domain/port အတိုင်းပြင်ပါ။ Port 8080 အသုံးပြုပြီးသားဆို `.env` ရဲ့ `PORT` ကို ပြောင်းပါ။ Game port က localhost ပဲ bind လုပ်ထားပါတယ်။

VPS user က Docker ကို run နိုင်ရပါမယ်။ GitHub အတွက် deployment SSH key သီးသန့်ဖန်တီးပြီး public key ကို VPS user ရဲ့ `authorized_keys` ထဲထည့်ပါ။ Private key ကို source code ထဲမတင်ပါနဲ့။

## GitHub ရဲ့ production environment

Repository → Settings → Environments → `production` ထဲမှာ secrets ထည့်ပါ:

| Secret | ထည့်ရမည့်တန်ဖိုး |
|---|---|
| `VPS_HOST` | VPS domain သို့မဟုတ် IPv4 လိပ်စာ |
| `VPS_USER` | `/opt/emberfall` နဲ့ Docker သုံးခွင့်ရှိတဲ့ SSH user |
| `VPS_PORT` | SSH port; မထည့်ရင် 22 |
| `VPS_SSH_KEY` | Deployment key ရဲ့ private key အပြည့်အစုံ |
| `VPS_KNOWN_HOSTS` | Fingerprint စစ်ပြီးသား server host key ပါတဲ့ known_hosts line |

Host key fingerprint ကို VPS console/ယုံကြည်ရတဲ့အကောင့်ကနေ `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` နဲ့ကြည့်ပြီး၊ ကိုယ့်ကွန်ပျူတာက SSH ချိတ်ချိန်ပြတဲ့ fingerprint နဲ့တိုက်စစ်ပါ။ ကိုယ့် `known_hosts` ထဲက အဲဒီ host အတွက် line ကိုသာ ကူးထည့်ပါ။ ပုံမှန်မဟုတ်တဲ့ port ဆို `[host]:port` ပုံစံဖြစ်ပါတယ်။ Workflow က host key မကိုက်ရင် ရပ်ပါတယ်။

`production` environment ကို main branch ပဲ deploy လုပ်ခွင့်ပေးထားနိုင်ပါတယ်။ Secret တွေကို chat ထဲ ပို့စရာမလိုပါဘူး။

## နောက်ပိုင်း deploy — GitHub ကနေ တစ်ချက်နှိပ်

1. Repository → Actions → **Deploy to VPS** ကိုဖွင့်ပါ။
2. **Run workflow** မှာ `main` ကိုရွေးပါ။
3. စမ်းသပ်ချက်တွေ အောင်မြင်ပြီးမှ image ထုတ်၊ verified SSH နဲ့ VPS ဆီပို့၊ database backup ယူ၊ game ပြောင်းတင်မယ်။
4. Game health check မအောင်မြင်ရင် ရှိပြီးသား image ကို ပြန်တင်မယ်။ Database volume ကို မဖျက်ပါဘူး။

ပထမ deploy မှာ rollback ပြန်တင်စရာ အဟောင်းမရှိသေးပါဘူး။ Workflow က game နဲ့ proxy process health ကိုစစ်ပါတယ်။ အင်တာနက်ကနေ DNS/HTTPS certificate အစစ်ရမရကို ကိုယ့် domain ဖွင့်ပြီးစစ်ပါ။ VPS ရှိရမယ်၊ setup လုပ်ထားရမယ်။ Source တင်လိုက်ရုံနဲ့ server အသစ်တစ်လုံး ရလာတာမဟုတ်ပါဘူး။

## ရှိပြီးသား v3 server မှ ပြောင်းခြင်း

v4 က v3 database နဲ့ လက်ရှိ Town Hall/Hero/Clan/progression ကို ဆက်သုံးနိုင်ပါတယ်။ အရင် backup ယူပါ။ လက်ရှိ data volume ရဲ့ Compose project နာမည်ကို သိမ်းထားပြီး `.env` ထဲမှာ:

```dotenv
COMPOSE_PROJECT_NAME=existing_project_name
```

အဲဒီနေရာမှာ တကယ့် project နာမည်ကိုထည့်ပါ။ ဥပမာ `emberfall_emberfall_data` volume သုံးနေရင် project က `emberfall` ပါ။ Workflow က နာမည်မကိုက်တဲ့ village volume အဟောင်းတွေ့ရင် အသစ်အလွတ်ရွာတစ်ခုနဲ့ မှားစမိတာ မဖြစ်အောင် ရပ်ပေးတယ်။

## Backup နှင့် rollback

Server စတင်ချိန်နဲ့ 6 နာရီတစ်ကြိမ် SQLite snapshot ယူပြီး integrity စစ်ပါတယ်။ Automatic snapshot 28 ခုထားပါတယ်။ Manual backup တွေကို auto retention က မဖျက်ပါဘူး။ Backup တွေက game data volume ထဲမှာရှိလို့ server တစ်ခုလုံးပျက်ရင် ကာကွယ်ဖို့ တခြားစက်/storage ဆီ ထပ်ကူးထားပါ။

Deploy ပြီးနောက် `/opt/emberfall/.deploy/current-image` နဲ့ `previous-image` မှာ release image ကိုမှတ်ထားမယ်။ ကူးပြောင်းရန်:

```sh
cd /opt/emberfall
bash scripts/deploy.sh "$(cat .deploy/previous-image)"
```

ဒီနည်းက code image ကို ပြန်တင်တာဖြစ်ပြီး database ကို အဟောင်းအဖြစ်ပြန်မပြောင်းပါဘူး။ Future release တွေမှာ database migration ပြောင်းလဲရင် အဲဒီ release ရဲ့ migration guide ကိုပါလိုက်နာရမယ်။

## GHCR image ထုတ်လိုလျှင်

`v4.0.0` လို `v` နဲ့စတဲ့ Git tag ကို push လုပ်ရင် စမ်းသပ်ချက်အောင်မြင်ပြီးမှ GitHub Container Registry ဆီ image ထုတ်ပေးမယ်။ Commit SHA tag နဲ့သိမ်းပါတယ်။ Registry က image သိမ်းတဲ့နေရာဖြစ်ပြီး game server ကို run ပေးတဲ့နေရာမဟုတ်ပါဘူး။ Default VPS workflow က image ကို SSH ကနေပို့တာဖြစ်လို့ GHCR access token ထပ်မလိုပါဘူး။

## စမ်းသပ်ပြီးမှုနှင့် အရင်းအမြစ်

Local automated checks 60 ခုမှာ gameplay, real HTTP/SQLite, security, wall economy, retry recovery, backup restore နှင့် simulated deployment failures ပါပါတယ်။ ဒီ build environment မှာ Docker binary မရှိလို့ Docker/SSH အစစ်ကို မ run ရသေးပါဘူး။ GitHub Actions မှာ အဲဒီ build/smoke test gate ထည့်ထားပါတယ်။ Live VPS, DNS, TLS နဲ့ payment အစစ် မစမ်းရသေးပါဘူး။

- [GitHub Pages static hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [GitHub Actions security](https://docs.github.com/en/actions/reference/security/secure-use)
- [Publishing Docker images](https://docs.github.com/actions/guides/publishing-docker-images)
- [GitHub Container Registry](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
