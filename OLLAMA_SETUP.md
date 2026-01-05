# Ollama Setup Guide - D Drive Installation

This guide will help you configure Ollama to store models on the D drive instead of the default C drive location.

## Step 1: Set Ollama Model Directory

Ollama stores models in a specific directory. On Windows, the default is `C:\Users\<username>\.ollama`. To change this to D drive:

### Option A: Set Environment Variable (Recommended)

1. **Create the Ollama directory on D drive:**
   ```bash
   mkdir D:\ollama
   mkdir D:\ollama\models
   ```

2. **Set the OLLAMA_MODELS environment variable:**

   **Via PowerShell (Temporary - current session only):**
   ```powershell
   $env:OLLAMA_MODELS="D:\ollama\models"
   ```

   **Via Command Prompt (Temporary - current session only):**
   ```cmd
   set OLLAMA_MODELS=D:\ollama\models
   ```

   **Permanently (System-wide):**

   a. Press `Win + X` and select "System"

   b. Click "Advanced system settings"

   c. Click "Environment Variables"

   d. Under "System variables" or "User variables", click "New"

   e. Set:
      - Variable name: `OLLAMA_MODELS`
      - Variable value: `D:\ollama\models`

   f. Click OK on all windows

   g. **Restart your terminal/command prompt** for changes to take effect

### Option B: Use Windows Registry (Alternative)

1. Open Registry Editor (`Win + R`, type `regedit`)

2. Navigate to:
   ```
   HKEY_CURRENT_USER\Environment
   ```

3. Right-click → New → String Value

4. Name: `OLLAMA_MODELS`

5. Value: `D:\ollama\models`

6. Restart your terminal

## Step 2: Install Ollama

If you haven't installed Ollama yet:

1. **Download Ollama for Windows:**
   - Visit: https://ollama.ai/download
   - Download the Windows installer

2. **Install Ollama:**
   - Run the installer (it will install the Ollama service)
   - The installation location is typically `C:\Program Files\Ollama`
   - But the **models** will be stored in the directory we configured above

## Step 3: Verify Configuration

1. **Check environment variable:**
   ```bash
   # PowerShell
   echo $env:OLLAMA_MODELS

   # Command Prompt
   echo %OLLAMA_MODELS%
   ```

   Should output: `D:\ollama\models`

2. **Start Ollama service:**
   ```bash
   ollama serve
   ```

   Or it may already be running as a Windows service.

## Step 4: Download Models to D Drive

Now when you download models, they'll be stored on D drive:

```bash
# Download llama2 (about 3.8 GB)
ollama pull llama2

# Or download a smaller model for testing
ollama pull llama2:7b

# Other popular models:
ollama pull mistral        # About 4.1 GB
ollama pull codellama      # About 3.8 GB
ollama pull llama2:13b     # About 7.4 GB (larger, more capable)
```

## Step 5: Verify Model Location

Check that models are stored on D drive:

```bash
# PowerShell
dir "D:\ollama\models\blobs\"

# Command Prompt
dir "D:\ollama\models\blobs\"
```

You should see files related to your downloaded models.

## Step 6: Update Talk For Me Configuration

Your `.env` file should already have the correct Ollama configuration:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

If you downloaded a different model, update `OLLAMA_MODEL` accordingly.

## Testing Ollama

1. **Test Ollama is running:**
   ```bash
   ollama list
   ```

   This should show your downloaded models.

2. **Test a model:**
   ```bash
   ollama run llama2 "Hello, how are you?"
   ```

3. **Test via API (what Talk For Me uses):**
   ```bash
   # PowerShell
   curl.exe http://localhost:11434/api/tags

   # Or use Invoke-WebRequest
   Invoke-WebRequest -Uri http://localhost:11434/api/tags
   ```

## Troubleshooting

### Models still downloading to C drive?

1. Make sure you **restarted your terminal** after setting the environment variable
2. Check the environment variable is set correctly:
   ```bash
   echo %OLLAMA_MODELS%    # CMD
   echo $env:OLLAMA_MODELS # PowerShell
   ```
3. If running Ollama as a Windows service, restart the service:
   ```bash
   # PowerShell (Run as Administrator)
   Restart-Service Ollama
   ```

### Ollama service not starting?

1. Check if Ollama is already running:
   ```bash
   # PowerShell
   Get-Process ollama
   ```

2. If it's running, you don't need to run `ollama serve` manually

3. Check Ollama service status:
   ```bash
   # PowerShell (Run as Administrator)
   Get-Service Ollama
   ```

### Port 11434 already in use?

If you get an error about port 11434:

1. Find what's using the port:
   ```bash
   # PowerShell
   Get-NetTCPConnection -LocalPort 11434
   ```

2. Stop the Ollama service and restart:
   ```bash
   # PowerShell (Run as Administrator)
   Stop-Service Ollama
   Start-Service Ollama
   ```

### Moving existing models from C drive to D drive

If you already have models on C drive:

1. **Find existing models:**
   ```bash
   dir "C:\Users\%USERNAME%\.ollama\models"
   ```

2. **Copy to D drive:**
   ```bash
   # Command Prompt
   xcopy "C:\Users\%USERNAME%\.ollama\models" "D:\ollama\models" /E /I /H

   # PowerShell
   Copy-Item -Path "$env:USERPROFILE\.ollama\models\*" -Destination "D:\ollama\models" -Recurse -Force
   ```

3. **Verify models appear in Ollama:**
   ```bash
   ollama list
   ```

4. **Optional: Delete old models from C drive** (after verifying D drive works):
   ```bash
   # Be careful! Double-check before running
   rmdir "C:\Users\%USERNAME%\.ollama\models" /S /Q
   ```

## Recommended Models for Talk For Me

Based on your use case (conversation suggestions), here are recommended models:

1. **llama2** (Default, Good balance)
   ```bash
   ollama pull llama2
   ```
   - Size: ~3.8 GB
   - Good for general conversation
   - Moderate speed

2. **mistral** (Better quality, slightly larger)
   ```bash
   ollama pull mistral
   ```
   - Size: ~4.1 GB
   - Better at conversation and context
   - Good instruction following

3. **llama2:7b** (Smaller, faster)
   ```bash
   ollama pull llama2:7b
   ```
   - Size: ~3.8 GB
   - Faster responses
   - Good for real-time suggestions

4. **phi** (Very small, very fast)
   ```bash
   ollama pull phi
   ```
   - Size: ~1.6 GB
   - Very fast responses
   - Good for quick suggestions
   - Less capable than larger models

## Quick Setup Script

Here's a complete setup script you can run:

```powershell
# PowerShell script to set up Ollama on D drive

# Create directory
New-Item -ItemType Directory -Force -Path "D:\ollama\models"

# Set environment variable for current session
$env:OLLAMA_MODELS = "D:\ollama\models"

# Set permanently (user level)
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\ollama\models", "User")

Write-Host "Environment variable set. Please restart your terminal."
Write-Host "After restarting, run: ollama pull llama2"
```

Save this as `setup_ollama.ps1` and run it in PowerShell.

## Next Steps

After setting up Ollama:

1. Verify the environment variable is set
2. Download your preferred model
3. Test Ollama with `ollama list` and `ollama run llama2 "test"`
4. Run Talk For Me: `python talk_for_me.py`

## Additional Resources

- Ollama Documentation: https://github.com/ollama/ollama/blob/main/docs/windows.md
- Model Library: https://ollama.ai/library
- Talk For Me README: [README.md](README.md)
