# Pydantic Metadata Error on Python 3.14 - Solutions

## 🔴 Error
```
error: metadata-generation-failed
× Encountered error while generating package metadata.
╰─> pydantic-core
```

## 🔍 Problem
Pydantic 2.7.0 cannot compile its C extensions on Python 3.14. This is a compatibility issue between Pydantic and Python 3.14.

---

## ✅ Solution #1: Use Minimal Requirements (RECOMMENDED)

```powershell
pip install -r requirements_MINIMAL.txt
```

**This skips Pydantic entirely** - it's not needed for your API!

Then run:
```powershell
python api_server_FINAL.py
```

---

## ✅ Solution #2: Downgrade to Python 3.13 (SAFEST)

Python 3.14 has breaking changes. Python 3.13 is more stable.

### 1. Download Python 3.13
- Go to https://www.python.org/downloads/
- Download Python 3.13.x
- Install it

### 2. Use Python 3.13
```powershell
# Check Python 3.13 is installed
py -3.13 --version

# Use Python 3.13 specifically
py -3.13 -m pip install -r requirements_FINAL.txt
py -3.13 api_server_FINAL.py
```

---

## ✅ Solution #3: Install Build Tools (ADVANCED)

Pydantic needs C compiler. Install build tools:

### Windows:
```powershell
pip install --upgrade setuptools wheel
pip install --upgrade pip
pip install -r requirements_FINAL.txt
```

Or install Visual C++ Build Tools from Microsoft.

---

## 🎯 RECOMMENDED APPROACH

### Step 1: Clean Install with Minimal Requirements
```powershell
# Remove all packages
pip uninstall -y flask flask-cors pypdf2 openai requests pydantic httpx urllib3 werkzeug

# Install minimal
pip install -r requirements_MINIMAL.txt
```

### Step 2: Run API
```powershell
python api_server_FINAL.py
```

**Should see:**
```
🚀 API Server Starting...
🌐 Running on http://localhost:5000
```

### Step 3: Test
```powershell
Invoke-WebRequest -Uri http://localhost:5000/health
```

---

## 📋 Why This Works

**requirements_MINIMAL.txt** contains:
```
Flask==3.0.3         ← Python 3.14 compatible
Flask-CORS==4.0.0    ← No compilation needed
PyPDF2==3.0.1        ← Pure Python
openai==1.52.0       ← Works with Python 3.14
python-dotenv==1.0.0 ← No compilation
requests==2.32.0     ← No compilation
```

**No Pydantic needed** - the API works without it!

---

## 🆘 If Minimal Still Fails

### Try installing one by one:
```powershell
pip install Flask==3.0.3
pip install Flask-CORS==4.0.0
pip install PyPDF2==3.0.1
pip install openai==1.52.0
pip install python-dotenv==1.0.0
pip install requests==2.32.0
```

Stop at whichever one fails.

---

## 💡 Why Python 3.14 Has Issues

- Python 3.14 removed deprecated features (`pkgutil.get_loader()`)
- Pydantic 2.7.0 uses C extensions that need compilation
- Compiler setup on Windows is complex
- Solution: Use Python 3.13 or skip Pydantic

---

## ✨ Your Setup

| File | Purpose |
|------|---------|
| **requirements_MINIMAL.txt** | ✅ Use this |
| **api_server_FINAL.py** | ✅ Use this |
| **file-upload-handler-enhanced.html** | ✅ Use this |
| **.env** | ✅ Your API key |

---

## 🚀 Final Command

```powershell
pip install -r requirements_MINIMAL.txt
python api_server_FINAL.py
```

Done! 🎉

---

## 🎯 If You Want to Use Python 3.14

1. Install Visual C++ Build Tools (complex)
2. Or downgrade to Python 3.13 (easier)

**Recommendation:** Use Python 3.13 - it's more stable and all packages work perfectly.
