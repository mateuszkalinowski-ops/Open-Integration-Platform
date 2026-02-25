# Building the Pinquark Nexo Agent Installer

## Prerequisites

1. **Inno Setup 6.x** — Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)
2. **WinSW** (Windows Service Wrapper) — Download `WinSW-x64.exe` from [GitHub releases](https://github.com/winsw/winsw/releases)

## Setup

### 1. Download WinSW

```powershell
# Download WinSW v3.x (64-bit) and place in the service/ directory
Invoke-WebRequest -Uri "https://github.com/winsw/winsw/releases/download/v3.0.0-alpha.11/WinSW-x64.exe" `
    -OutFile "service\WinSW.exe"
```

### 2. Prepare icon and banner images

Place the following files in the `assets/` directory:

| File | Size | Description |
|---|---|---|
| `pinquark-nexo.ico` | 256x256 | Application icon (ICO format, multi-size) |
| `wizard-banner.bmp` | 164x314 | Wizard sidebar image (BMP format) |
| `wizard-small.bmp` | 55x55 | Wizard header logo (BMP format) |

If you don't have these yet, create placeholder images:

```powershell
# Create a minimal valid ICO (placeholder)
# For production, use proper branded graphics
```

### 3. Build the installer

```powershell
# Option A: Using Inno Setup GUI
# Open nexo-agent-setup.iss in Inno Setup Compiler and click Build > Compile

# Option B: Using command line (iscc.exe)
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" nexo-agent-setup.iss
```

### 4. Output

The installer will be created at:
```
Output\PinquarkNexoAgentSetup_1.0.0.exe
```

## Installer Contents

The generated EXE includes:

| Component | Source | Destination |
|---|---|---|
| Python application | `../src/` | `{app}\src\` |
| Requirements | `../requirements.txt` | `{app}\` |
| Gunicorn config | `../gunicorn.conf.py` | `{app}\` |
| Connector manifest | `../connector.yaml` | `{app}\` |
| WinSW service wrapper | `service\WinSW.exe` | `{app}\service\nexo-agent-service.exe` |
| Service config | `service\nexo-agent-service.xml` | `{app}\service\` |
| Management scripts | `scripts\*` | `{app}\scripts\` + `{app}\` |
| Icon | `assets\pinquark-nexo.ico` | `{app}\assets\` |

## What the Installer Does

### Installation wizard flow:

1. **Welcome** — License agreement (Apache 2.0)
2. **Install directory** — Default: `C:\Program Files\Pinquark\NexoAgent`
3. **Prerequisites check** — Validates Python 3.12+ and .NET 8.0 Runtime
4. **SDK path** — Locate InsERT Nexo SDK Bin directory
5. **SQL Server** — Server instance, database name, auth mode
6. **Nexo operator** — Login, password, module (Subiekt)
7. **Warehouse** — Default warehouse symbol, branch, agent ID
8. **Cloud connection** — Platform URL, API key, sync intervals
9. **Service mode** — Install as Windows Service or manual mode
10. **Install** — Copy files, install pip dependencies, configure service

### Post-install actions:

- Creates `data/` and `logs/` directories
- Generates `.env` from wizard values
- Runs `pip install -r requirements.txt`
- Installs and starts Windows Service (if selected)

### Uninstall:

- Stops the Windows Service
- Removes the service registration
- Deletes application files (preserves `data/` and `logs/`)

## Silent Installation

For automated deployments, use the Inno Setup `/SILENT` or `/VERYSILENT` flags:

```powershell
PinquarkNexoAgentSetup_1.0.0.exe /VERYSILENT /DIR="C:\Pinquark\NexoAgent"
```

After silent install, configure manually:

```powershell
cd "C:\Pinquark\NexoAgent\scripts"
.\configure-agent.ps1
.\install-service.ps1
```

## Alternative: Manual Installation (No Installer)

```powershell
# 1. Copy files
xcopy /E /I ..\src C:\Pinquark\NexoAgent\src
copy ..\requirements.txt C:\Pinquark\NexoAgent\
copy ..\gunicorn.conf.py C:\Pinquark\NexoAgent\

# 2. Install dependencies
cd C:\Pinquark\NexoAgent
python -m pip install -r requirements.txt

# 3. Configure
copy scripts\configure-agent.ps1 .
.\configure-agent.ps1

# 4. Run (manual)
.\scripts\start-agent.bat

# 4b. Or install as service
.\scripts\install-service.ps1
```
