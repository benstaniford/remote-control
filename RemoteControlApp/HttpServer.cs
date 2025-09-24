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
        private Task _listenerTask;

        public HttpServer(ShellManager shellManager)
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add("http://localhost:8417/");
            _cancellationTokenSource = new CancellationTokenSource();
            _shellManager = shellManager;
        }

        public void Start()
        {
            _listener.Start();
            _listenerTask = Task.Run(async () => await ListenForRequests(_cancellationTokenSource.Token));
        }

        public void Stop()
        {
            _cancellationTokenSource.Cancel();
            _listener.Stop();
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
            try
            {
                var request = context.Request;
                var response = context.Response;

                response.Headers.Add("Access-Control-Allow-Origin", "*");
                response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
                response.Headers.Add("Access-Control-Allow-Headers", "Content-Type");

                if (request.HttpMethod == "OPTIONS")
                {
                    response.StatusCode = 200;
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

                    var responseText = ProcessCommand(requestBody);
                    var buffer = Encoding.UTF8.GetBytes(responseText);

                    response.ContentType = "application/json";
                    response.ContentLength64 = buffer.Length;
                    response.StatusCode = 200;

                    using (var output = response.OutputStream)
                    {
                        output.Write(buffer, 0, buffer.Length);
                    }
                }
                else
                {
                    response.StatusCode = 405;
                }

                response.Close();
            }
            catch (Exception ex)
            {
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
                            return CreateJsonResponse(false, "URL is required");
                        }

                        BrowserLauncher.LaunchUrl(url);
                        return CreateJsonResponse(true, "Browser launched successfully");

                    case "shell_start":
                        try
                        {
                            _shellManager.StartShell();
                            return CreateJsonResponse(true, "Shell started successfully");
                        }
                        catch (Exception ex)
                        {
                            return CreateJsonResponse(false, "Failed to start shell: " + ex.Message);
                        }

                    case "shell_input":
                        var input = ExtractJsonValue(jsonCommand, "input");
                        if (input == null)
                        {
                            return CreateJsonResponse(false, "Input is required");
                        }

                        try
                        {
                            _shellManager.SendInput(input);
                            return CreateJsonResponse(true, "Input sent successfully");
                        }
                        catch (Exception ex)
                        {
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
                            _shellManager.StopShell();
                            return CreateJsonResponse(true, "Shell stopped successfully");
                        }
                        catch (Exception ex)
                        {
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
                // Simple regex-based JSON value extraction for basic cases
                var pattern = "\"" + key + "\"\\s*:\\s*\"([^\"]*)\"";
                var match = Regex.Match(json, pattern, RegexOptions.IgnoreCase);
                return match.Success ? match.Groups[1].Value : null;
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