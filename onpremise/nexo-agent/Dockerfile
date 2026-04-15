# --- Build stage ---
FROM mcr.microsoft.com/windows/servercore:ltsc2022 AS build

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]

# Install Python 3.12
RUN Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile python-installer.exe; \
    Start-Process python-installer.exe -Wait -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1'; \
    Remove-Item python-installer.exe

# Install .NET 8.0 Runtime (required by Nexo SDK)
RUN Invoke-WebRequest -Uri 'https://dot.net/v1/dotnet-install.ps1' -OutFile dotnet-install.ps1; \
    ./dotnet-install.ps1 -Runtime dotnet -Version 8.0.11 -InstallDir 'C:\dotnet'; \
    Remove-Item dotnet-install.ps1

ENV DOTNET_ROOT=C:\dotnet
ENV PATH="C:\dotnet;C:\Python312;C:\Python312\Scripts;${PATH}"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# --- Production stage ---
FROM mcr.microsoft.com/windows/servercore:ltsc2022

LABEL maintainer="integrations@pinquark.com"
LABEL version="1.0.0"
LABEL category="erp"
LABEL system="insert-nexo"
LABEL deployment="on-premise"


RUN apt-get update -qq && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]

# Install Python 3.12
RUN Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile python-installer.exe; \
    Start-Process python-installer.exe -Wait -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1'; \
    Remove-Item python-installer.exe

# Install .NET 8.0 Runtime
RUN Invoke-WebRequest -Uri 'https://dot.net/v1/dotnet-install.ps1' -OutFile dotnet-install.ps1; \
    ./dotnet-install.ps1 -Runtime dotnet -Version 8.0.11 -InstallDir 'C:\dotnet'; \
    Remove-Item dotnet-install.ps1

ENV DOTNET_ROOT=C:\dotnet
ENV PATH="C:\dotnet;C:\Python312;C:\Python312\Scripts;${PATH}"
ENV PYTHONNET_RUNTIME=coreclr

WORKDIR /app

COPY --from=build /app .

# SDK DLLs are mounted at runtime via volume
# docker run -v C:\nexoSDK\Bin:C:\nexo-sdk:ro ...
ENV NEXO_SDK_BIN_PATH=C:\nexo-sdk

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD powershell -Command "try { $r = Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"

ENTRYPOINT ["python", "-m", "gunicorn", "--config", "gunicorn.conf.py", "src.main:app"]
