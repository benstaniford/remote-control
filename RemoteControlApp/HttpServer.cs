using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace RemoteControlApp
{
    public class HttpServer : IDisposable
    {
        private readonly HttpListener _listener;
        private readonly CancellationTokenSource _cancellationTokenSource;
        private Task _listenerTask;

        public HttpServer()
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add("http://localhost:417/");
            _cancellationTokenSource = new CancellationTokenSource();
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
                    var errorResponse = JsonConvert.SerializeObject(new { error = ex.Message });
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
                dynamic command = JsonConvert.DeserializeObject(jsonCommand);
                string action = command.action;

                switch (action?.ToLower())
                {
                    case "launch_browser":
                        string url = command.url;
                        if (string.IsNullOrEmpty(url))
                        {
                            return JsonConvert.SerializeObject(new { success = false, error = "URL is required" });
                        }
                        
                        BrowserLauncher.LaunchUrl(url);
                        return JsonConvert.SerializeObject(new { success = true, message = "Browser launched successfully" });

                    default:
                        return JsonConvert.SerializeObject(new { success = false, error = "Unknown action" });
                }
            }
            catch (Exception ex)
            {
                return JsonConvert.SerializeObject(new { success = false, error = ex.Message });
            }
        }

        public void Dispose()
        {
            Stop();
            _cancellationTokenSource?.Dispose();
            _listener?.Close();
        }
    }
}