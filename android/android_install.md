# Android Installation Guide

This guide will walk you through setting up the PocketOption Signal Generator on your Android device using Termux. The application will run in the background and send trading signals to your Telegram group.

## Prerequisites
- Android 7.0 or higher
- 500MB free storage
- Stable internet connection
- Telegram account with admin access to your group

## Step 1: Install Required Apps
1. **Install Termux**:
   - Download from [F-Droid](https://f-droid.org/repo/com.termux_117.apk) (recommended) or [GitHub](https://github.com/termux/termux-app/releases)
   - *Do not install from Play Store - it has outdated versions*

2. **Install Termux:API** (for battery optimization bypass):
   - [F-Droid](https://f-droid.org/repo/com.termux.api_51.apk)
   - [GitHub](https://github.com/termux/termux-api/releases)

3. **Install a File Manager**:
   - [Mixplorer](https://mixplorer.com/) or [Solid Explorer](https://play.google.com/store/apps/details?id=pl.solidexplorer2)

## Step 2: Initial Termux Setup
```bash
# 1. Launch Termux and run:
termux-setup-storage

# 2. Update packages:
pkg update -y && pkg upgrade -y

# 3. Install essential tools:
pkg install -y git python wget nano proot

# 4. Install Python dependencies:
pip install wheel setuptools
