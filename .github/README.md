<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">
</p>

<h1 align="center">🎵 Telegram Music Bot API</h1>
<p align="center">
  Stream Audio & Video in your Telegram Music Bots — fast, secure, and cookie-free.
</p>
<p align="center">
  <img src="https://img.shields.io/badge/license-Commercial-red.svg" alt="License Badge">
</p>

---

## 🚀 Overview

Introducing a **robust API** for Telegram Music Bots that allows **audio & video playback** with **zero cookies** and **minimal errors**. This API is designed for **developers, music bot owners**, and anyone building scalable music systems on Telegram.

---

## ✨ Features

- ✅ Audio & Video Streaming Support  
- ✅ Cookie-free & Error-free Playback  
- ✅ API Key Based Access  
- ✅ Flexible Rate Limits  
- ✅ Affordable Monthly Plans  
- ✅ Easy Integration (Python, Node.js, C++, etc.)

---

## 💰 Pricing & Plans

<!-- PRICING_START -->
| 💼 Plan | ⚡ Rate Limit | 💵 Price (INR/month) | 💰 Discount |
|---------|--------------|---------------------|-------------|
| 🆓 **Free** | 150 requests/day | ₹0 | - |
| 🟢 **Lite** | 1,500 requests/day | ₹49 | 35% OFF |
| 🔵 **Basic** | 3,000 requests/day | ₹99 | 40% OFF |
| 🟡 **Starter** | 5,000 requests/day | ₹149 | 50% OFF |
| 🟣 **Standard** | 10,000 requests/day | ₹289 | 45% OFF |
| 🔴 **Pro** | 25,000 requests/day | ₹569 | 50% OFF |
| 🟠 **Business** | 50,000 requests/day | ₹1,129 | - |
| ⚫ **Enterprise** | 100,000 requests/day | ₹1,879 | - |
| 💎 **Ultra** | 150,000 requests/day | ₹2,389 | - |
| 🚀 **Business lite** | 35,000 requests/day | ₹854 | 35% OFF |
<!-- PRICING_END -->

> Prices may vary. For the latest pricing, visit [music.xbitcode.com](https://music.xbitcode.com/#pricing)

---



## ⚙️ API Usage

**Base Endpoint**

🔑 API Access Key

> Online Documentation: [music.xbitcode.com/dashboard/docs](https://music.xbitcode.com/dashboard/docs)
> Get your API key from: [music.xbitcode.com](https://music.xbitcode.com/auth/signin)
> Use your key in config.py
> API key pattern: `xbit_10000000xx0233`


---

## ⚡️ Getting Started [[Documentation](https://stranger-organization.gitbook.io/stranger-music-docs/local-vps-deploy)]

---

## 📞 Contact & Support

Need help or want to subscribe?

- **Website:** [music.xbitcode.com](https://music.xbitcode.com)
- **Telegram Channel:** [@BLACKFIREBOOYAHCUP](https://t.me/BLACKFIREBOOYAHCUP)
- **Telegram Group:** [@AeraxTi](https://t.me/AeraxTi)
- **Telegram User:** [@ade2321czf](https://t.me/ade2321czf)
- **API & Promotions:** [Api_and_promotion](https://t.me/Api_and_promotion)

**Maintained by:** [Xbitcode](https://xbitcode.com/)

---

## ⚠️ Disclaimer

This service is intended for personal and educational use.
Users must follow YouTube's Terms of Service and Telegram's Bot Policy.

---

<h2 align="center">
    ──「 Telegram Music Bot 」──
</h2>

<h3 align="center">
    ─「 ᴅᴇᴩʟᴏʏ ᴏɴ ʜᴇʀᴏᴋᴜ 」─
</h3>

<p align="center"><a href="https://dashboard.heroku.com/new?template=https://github.com/xbitcode/music"> <img src="https://img.shields.io/badge/Deploy%20On%20Heroku-purple?style=for-the-badge&logo=heroku" width="220" height="38.45"/></a></p>

<h3 align="center">
    ─「 ᴅᴇᴩʟᴏʏ ᴏɴ ʟᴏᴄᴀʟ ʜᴏsᴛ/ ᴠᴘs 」─
</h3>

- Get your [Necessary Variables](https://github.com/xbitcode/music/blob/main/sample.env)

```bash
# Clone the repository
git clone https://github.com/xbitcode/music && cd music

# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install ffmpeg
sudo apt-get install ffmpeg -y

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Create virtual environment and install dependencies
uv venv && uv sync

# Set up your environment variables
cp sample.env .env
vi .env
