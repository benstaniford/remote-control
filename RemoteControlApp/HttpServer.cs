using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Text.RegularExpressions;

namespace RemoteControlApp
{
    public class HttpServer : IDisposable
    {
        private readonly HttpListener _listener;
        private readonly CancellationTokenSource _cancellationTokenSource;
        private readonly ShellManager _shellManager;
        private readonly FileManager _fileManager;
        private Task _listenerTask;

        public HttpServer(ShellManager shellManager, FileManager fileManager)
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add("http://localhost:8417/");
            _cancellationTokenSource = new CancellationTokenSource();
            _shellManager = shellManager;
            _fileManager = fileManager;
        }

        public void Start()
        {
            _listener.Start();
            Logger.LogInfo("HTTP Server started on localhost:8417");
            _listenerTask = Task.Run(async () => await ListenForRequests(_cancellationTokenSource.Token));
        }

        public void Stop()
        {
            _cancellationTokenSource.Cancel();
            _listener.Stop();
            Logger.LogInfo("HTTP Server stopped");
            _listenerTask?.Wait(5000);
        }

        private async Task ListenForRequests(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    var context = await _listener.GetContextAsync();
                    _ = Task.Run(() => ProcessRequest(context), cancellationToken);
                }
                catch (HttpListenerException)
                {
                    break;
                }
                catch (ObjectDisposedException)
                {
                    break;
                }
            }
        }

        private void ProcessRequest(HttpListenerContext context)
        {
            var clientIP = context.Request.RemoteEndPoint?.Address?.ToString();
            var userAgent = context.Request.UserAgent;
            
            try
            {
                var request = context.Request;
                var response = context.Response;

                Logger.LogRequest(request.HttpMethod, "REQUEST_RECEIVED", $"From: {clientIP}, UserAgent: {userAgent}");

                response.Headers.Add("Access-Control-Allow-Origin", "*");
                response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
                response.Headers.Add("Access-Control-Allow-Headers", "Content-Type");

                if (request.HttpMethod == "OPTIONS")
                {
                    response.StatusCode = 200;
                    Logger.LogRequest("OPTIONS", "PREFLIGHT", "CORS preflight request handled");
                    response.Close();
                    return;
                }

                if (request.HttpMethod == "POST")
                {
                    string requestBody;
                    using (var reader = new StreamReader(request.InputStream, request.ContentEncoding))
                    {
                        requestBody = reader.ReadToEnd();
                    }

                    Logger.LogRequest("POST", "COMMAND_RECEIVED", $"Body length: {requestBody.Length} characters");

                    var responseText = ProcessCommand(requestBody);
                    var buffer = Encoding.UTF8.GetBytes(responseText);

                    response.ContentType = "application/json";
                    response.ContentLength64 = buffer.Length;
                    response.StatusCode = 200;

                    Logger.LogRequest("POST", "RESPONSE_SENT", $"Response length: {buffer.Length} bytes, Status: 200");

                    using (var output = response.OutputStream)
                    {
                        output.Write(buffer, 0, buffer.Length);
                    }
                }
                else
                {
                    response.StatusCode = 405;
                    Logger.LogRequest(request.HttpMethod, "METHOD_NOT_ALLOWED", $"Unsupported method: {request.HttpMethod}");
                }

                response.Close();
            }
            catch (Exception ex)
            {
                Logger.LogError($"Request processing failed: {ex.Message}");
                try
                {
                    var errorResponse = CreateJsonResponse(false, ex.Message);
                    var buffer = Encoding.UTF8.GetBytes(errorResponse);
                    context.Response.StatusCode = 500;
                    context.Response.ContentType = "application/json";
                    context.Response.ContentLength64 = buffer.Length;
                    using (var output = context.Response.OutputStream)
                    {
                        output.Write(buffer, 0, buffer.Length);
                    }
                    Logger.LogRequest("ERROR", "ERROR_RESPONSE", $"Status: 500, Error: {ex.Message}");
                    context.Response.Close();
                }
                catch { }
            }
        }

        private string ProcessCommand(string jsonCommand)
        {
            try
            {
                // Simple JSON parsing for specific structure
                var action = ExtractJsonValue(jsonCommand, "action");

                if (string.IsNullOrEmpty(action))
                {
                    return CreateJsonResponse(false, "Action is required");
                }

                switch (action.ToLower())
                {
                    case "launch_browser":
                        var url = ExtractJsonValue(jsonCommand, "url");
                        if (string.IsNullOrEmpty(url))
                        {
                            Logger.LogRequest("POST", "launch_browser", "ERROR: URL is required");
                            return CreateJsonResponse(false, "URL is required");
                        }

                        Logger.LogRequest("POST", "launch_browser", $"URL: {url}");
                        BrowserLauncher.LaunchUrl(url);
                        Logger.LogAction("BROWSER_LAUNCHED", $"Successfully launched: {url}");
                        return CreateJsonResponse(true, "Browser launched successfully");

                    case "shell_start":
                        try
                        {
                            var workingDirectory = ExtractJsonValue(jsonCommand, "working_directory");
                            Logger.LogRequest("POST", "shell_start", $"Working directory: {workingDirectory ?? "default"}");
                            _shellManager.StartShell(workingDirectory);
                            Logger.LogAction("SHELL_STARTED", $"Working directory: {workingDirectory ?? "default"}");
                            return CreateJsonResponse(true, "Shell started successfully");
                        }
                        catch (Exception ex)
                        {
                            Logger.LogError($"Failed to start shell: {ex.Message}");
                            return CreateJsonResponse(false, "Failed to start shell: " + ex.Message);
                        }

                    case "shell_input":
                        var input = ExtractJsonValue(jsonCommand, "input");
                        if (input == null)
                        {
                            Logger.LogRequest("POST", "shell_input", "ERROR: Input is required");
                            return CreateJsonResponse(false, "Input is required");
                        }

                        try
                        {
                            Logger.LogRequest("POST", "shell_input", $"Command: {input}");
                            _shellManager.SendInput(input);
                            Logger.LogAction("SHELL_COMMAND", $"Executed: {input}");
                            return CreateJsonResponse(true, "Input sent successfully");
                        }
                        catch (InvalidOperationException ex) when (ex.Message.Contains("Shell is not running"))
                        {
                            Logger.LogWarning($"Shell was dead, attempting auto-restart for command: {input}");
                            try
                            {
                                if (_shellManager.TryAutoRestart())
                                {
                                    _shellManager.SendInput(input);
                                    Logger.LogAction("SHELL_COMMAND_AFTER_RESTART", $"Executed after restart: {input}");
                                    return CreateJsonResponse(true, "Input sent successfully (after restart)");
                                }
                                else
                                {
                                    Logger.LogError("Auto-restart failed");
                                    return CreateJsonResponse(false, "Shell is not running and restart failed");
                                }
                            }
                            catch (Exception restartEx)
                            {
                                Logger.LogError($"Failed to restart shell: {restartEx.Message}");
                                return CreateJsonResponse(false, "Shell is not running and restart failed: " + restartEx.Message);
                            }
                        }
                        catch (Exception ex)
                        {
                            Logger.LogError($"Failed to send shell input: {ex.Message}");
                            return CreateJsonResponse(false, "Failed to send input: " + ex.Message);
                        }

                    case "shell_output":
                        try
                        {
                            var output = _shellManager.GetOutput();
                            var error = _shellManager.GetError();
                            return CreateShellOutputResponse(output, error);
                        }
                        catch (Exception ex)
                        {
                            return CreateJsonResponse(false, "Failed to get output: " + ex.Message);
                        }

                    case "shell_stop":
                        try
                        {
                            Logger.LogRequest("POST", "shell_stop", "Stopping shell");
                            _shellManager.StopShell();
                            Logger.LogAction("SHELL_STOPPED", "Shell terminated successfully");
                            return CreateJsonResponse(true, "Shell stopped successfully");
                        }
                        catch (Exception ex)
                        {
                            Logger.LogError($"Failed to stop shell: {ex.Message}");
                            return CreateJsonResponse(false, "Failed to stop shell: " + ex.Message);
                        }

                    case "shell_status":
                        try
                        {
                            var isRunning = _shellManager.IsRunning;
                            return CreateShellStatusResponse(isRunning);
                        }
                        catch (Exception ex)
                        {
                            return CreateJsonResponse(false, "Failed to get shell status: " + ex.Message);
                        }

                    case "shell_cd":
                        var directory = ExtractJsonValue(jsonCommand, "directory");
                        if (string.IsNullOrEmpty(directory))
                        {
                            return CreateJsonResponse(false, "Directory path is required");
                        }

                        try
                        {
                            _shellManager.SendInput($"cd /d \"{directory}\"");
                            return CreateJsonResponse(true, "Changed directory successfully");
                        }
                        catch (Exception ex)
                        {
                            return CreateJsonResponse(false, "Failed to change directory: " + ex.Message);
                        }

                    case "file_upload":
                        var uploadPath = ExtractJsonValue(jsonCommand, "path");
                        var uploadContent = ExtractJsonValue(jsonCommand, "content");
                        if (string.IsNullOrEmpty(uploadPath))
                        {
                            Logger.LogRequest("POST", "file_upload", "ERROR: File path is required");
                            return CreateJsonResponse(false, "File path is required");
                        }
                        if (string.IsNullOrEmpty(uploadContent))
                        {
                            Logger.LogRequest("POST", "file_upload", "ERROR: File content is required");
                            return CreateJsonResponse(false, "File content is required");
                        }

                        try
                        {
                            Logger.LogRequest("POST", "file_upload", $"Path: {uploadPath}, Content size: {uploadContent.Length} chars");
                            _fileManager.WriteFileFromBase64(uploadPath, uploadContent);
                            Logger.LogAction("FILE_UPLOADED", $"Successfully uploaded to: {uploadPath}");
                            return CreateJsonResponse(true, "File uploaded successfully");
                        }
                        catch (Exception ex)
                        {
                            Logger.LogError($"Failed to upload file {uploadPath}: {ex.Message}");
                            return CreateJsonResponse(false, "Failed to upload file: " + ex.Message);
                        }

                    case "file_download":
                        var downloadPath = ExtractJsonValue(jsonCommand, "path");
                        if (string.IsNullOrEmpty(downloadPath))
                        {
                            Logger.LogRequest("POST", "file_download", "ERROR: File path is required");
                            return CreateJsonResponse(false, "File path is required");
                        }

                        try
                        {
                            Logger.LogRequest("POST", "file_download", $"Path: {downloadPath}");
                            var fileContent = _fileManager.ReadFileAsBase64(downloadPath);
                            var fileInfo = _fileManager.GetFileInfo(downloadPath);
                            Logger.LogAction("FILE_DOWNLOADED", $"Successfully downloaded: {downloadPath}, Size: {fileInfo.Length} bytes");
                            return CreateFileDownloadResponse(fileContent, fileInfo);
                        }
                        catch (Exception ex)
                        {
                            Logger.LogError($"Failed to download file {downloadPath}: {ex.Message}");
                            return CreateJsonResponse(false, "Failed to download file: " + ex.Message);
                        }

                    case "file_exists":
                        var checkPath = ExtractJsonValue(jsonCommand, "path");
                        if (string.IsNullOrEmpty(checkPath))
                        {
                            return CreateJsonResponse(false, "File path is required");
                        }

                        try
                        {
                            var exists = _fileManager.FileExists(checkPath);
                            return CreateFileExistsResponse(exists);
                        }
                        catch (Exception ex)
                        {
                            return CreateJsonResponse(false, "Failed to check file: " + ex.Message);
                        }

                    case "file_info":
                        var infoPath = ExtractJsonValue(jsonCommand, "path");
                        if (string.IsNullOrEmpty(infoPath))
                        {
                            return CreateJsonResponse(false, "File path is required");
                        }

                        try
                        {
                            var fileInfo = _fileManager.GetFileInfo(infoPath);
                            var fileHash = _fileManager.GetFileHash(infoPath);
                            return CreateFileInfoResponse(fileInfo, fileHash);
                        }
                        catch (Exception ex)
                        {
                            return CreateJsonResponse(false, "Failed to get file info: " + ex.Message);
                        }

                    case "file_delete":
                        var deletePath = ExtractJsonValue(jsonCommand, "path");
                        if (string.IsNullOrEmpty(deletePath))
                        {
                            Logger.LogRequest("POST", "file_delete", "ERROR: File path is required");
                            return CreateJsonResponse(false, "File path is required");
                        }

                        try
                        {
                            Logger.LogRequest("POST", "file_delete", $"Path: {deletePath}");
                            _fileManager.DeleteFile(deletePath);
                            Logger.LogAction("FILE_DELETED", $"Successfully deleted: {deletePath}");
                            return CreateJsonResponse(true, "File deleted successfully");
                        }
                        catch (Exception ex)
                        {
                            Logger.LogError($"Failed to delete file {deletePath}: {ex.Message}");
                            return CreateJsonResponse(false, "Failed to delete file: " + ex.Message);
                        }

                    case "file_list":
                        var listPath = ExtractJsonValue(jsonCommand, "path");
                        var pattern = ExtractJsonValue(jsonCommand, "pattern");
                        if (string.IsNullOrEmpty(listPath))
                        {
                            return CreateJsonResponse(false, "Directory path is required");
                        }

                        try
                        {
                            var files = _fileManager.ListFiles(listPath, pattern ?? "*");
                            return CreateFileListResponse(files);
                        }
                        catch (Exception ex)
                        {
                            return CreateJsonResponse(false, "Failed to list files: " + ex.Message);
                        }

                    default:
                        return CreateJsonResponse(false, "Unknown action");
                }
            }
            catch (Exception ex)
            {
                return CreateJsonResponse(false, ex.Message);
            }
        }

        private string ExtractJsonValue(string json, string key)
        {
            try
            {
                // Find the key in the JSON
                var keyPattern = "\"" + key + "\"\\s*:\\s*\"";
                var keyMatch = Regex.Match(json, keyPattern, RegexOptions.IgnoreCase);
                if (!keyMatch.Success)
                    return null;

                // Start position after the opening quote of the value
                int startPos = keyMatch.Index + keyMatch.Length;
                
                // Find the closing quote, handling escaped quotes
                StringBuilder value = new StringBuilder();
                bool escapeNext = false;
                
                for (int i = startPos; i < json.Length; i++)
                {
                    char c = json[i];
                    
                    if (escapeNext)
                    {
                        // Add the escaped character (handle common JSON escapes)
                        switch (c)
                        {
                            case 'n': value.Append('\n'); break;
                            case 'r': value.Append('\r'); break;
                            case 't': value.Append('\t'); break;
                            case '\\': value.Append('\\'); break;
                            case '"': value.Append('"'); break;
                            case '/': value.Append('/'); break;
                            default: 
                                value.Append('\\');
                                value.Append(c);
                                break;
                        }
                        escapeNext = false;
                    }
                    else if (c == '\\')
                    {
                        escapeNext = true;
                    }
                    else if (c == '"')
                    {
                        // Found the closing quote
                        return value.ToString();
                    }
                    else
                    {
                        value.Append(c);
                    }
                }
                
                // If we get here, no closing quote was found
                return null;
            }
            catch
            {
                return null;
            }
        }

        private string CreateJsonResponse(bool success, string message)
        {
            if (success)
            {
                return "{\"success\": true, \"message\": \"" + EscapeJsonString(message) + "\"}";
            }
            else
            {
                return "{\"success\": false, \"error\": \"" + EscapeJsonString(message) + "\"}";
            }
        }

        private string CreateShellOutputResponse(string output, string error)
        {
            var outputJson = string.IsNullOrEmpty(output) ? "\"\"" : "\"" + EscapeJsonString(output) + "\"";
            var errorJson = string.IsNullOrEmpty(error) ? "\"\"" : "\"" + EscapeJsonString(error) + "\"";
            
            return "{\"success\": true, \"output\": " + outputJson + ", \"error\": " + errorJson + "}";
        }

        private string CreateShellStatusResponse(bool isRunning)
        {
            return "{\"success\": true, \"running\": " + (isRunning ? "true" : "false") + "}";
        }

        private string CreateFileDownloadResponse(string content, FileInfo fileInfo)
        {
            var contentJson = "\"" + EscapeJsonString(content) + "\"";
            var nameJson = "\"" + EscapeJsonString(fileInfo.Name) + "\"";
            var sizeJson = fileInfo.Length.ToString();
            var modifiedJson = "\"" + fileInfo.LastWriteTime.ToString("yyyy-MM-ddTHH:mm:ss.fffZ") + "\"";
            
            return "{\"success\": true, \"content\": " + contentJson + ", \"name\": " + nameJson + ", \"size\": " + sizeJson + ", \"modified\": " + modifiedJson + "}";
        }

        private string CreateFileExistsResponse(bool exists)
        {
            return "{\"success\": true, \"exists\": " + (exists ? "true" : "false") + "}";
        }

        private string CreateFileInfoResponse(FileInfo fileInfo, string hash)
        {
            var nameJson = "\"" + EscapeJsonString(fileInfo.Name) + "\"";
            var fullNameJson = "\"" + EscapeJsonString(fileInfo.FullName) + "\"";
            var sizeJson = fileInfo.Length.ToString();
            var createdJson = "\"" + fileInfo.CreationTime.ToString("yyyy-MM-ddTHH:mm:ss.fffZ") + "\"";
            var modifiedJson = "\"" + fileInfo.LastWriteTime.ToString("yyyy-MM-ddTHH:mm:ss.fffZ") + "\"";
            var hashJson = "\"" + EscapeJsonString(hash) + "\"";
            
            return "{\"success\": true, \"name\": " + nameJson + ", \"fullName\": " + fullNameJson + ", \"size\": " + sizeJson + ", \"created\": " + createdJson + ", \"modified\": " + modifiedJson + ", \"hash\": " + hashJson + "}";
        }

        private string CreateFileListResponse(string[] files)
        {
            var fileList = new StringBuilder();
            fileList.Append("[");
            
            for (int i = 0; i < files.Length; i++)
            {
                if (i > 0) fileList.Append(", ");
                fileList.Append("\"" + EscapeJsonString(files[i]) + "\"");
            }
            
            fileList.Append("]");
            return "{\"success\": true, \"files\": " + fileList.ToString() + "}";
        }

        private string EscapeJsonString(string input)
        {
            if (string.IsNullOrEmpty(input))
                return input;

            return input
                .Replace("\\", "\\\\")
                .Replace("\"", "\\\"")
                .Replace("\r", "\\r")
                .Replace("\n", "\\n")
                .Replace("\t", "\\t");
        }

        public void Dispose()
        {
            Stop();
            _cancellationTokenSource?.Dispose();
            _listener?.Close();
        }
    }
}