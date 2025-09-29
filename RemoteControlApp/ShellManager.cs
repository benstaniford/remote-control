using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Concurrent;

namespace RemoteControlApp
{
    public class ShellManager : IDisposable
    {
        private Process _shellProcess;
        private StreamWriter _shellInput;
        private readonly ConcurrentQueue<string> _outputBuffer;
        private readonly ConcurrentQueue<string> _errorBuffer;
        private readonly CancellationTokenSource _cancellationTokenSource;
        private Task _outputReaderTask;
        private Task _errorReaderTask;
        private readonly object _processLock = new object();

        public bool IsRunning { get; private set; }

        public ShellManager()
        {
            _outputBuffer = new ConcurrentQueue<string>();
            _errorBuffer = new ConcurrentQueue<string>();
            _cancellationTokenSource = new CancellationTokenSource();
        }

        public void StartShell(string workingDirectory = null)
        {
            lock (_processLock)
            {
                if (IsRunning)
                {
                    Logger.LogWarning("Shell start requested but shell is already running");
                    return;
                }

                try
                {
                    var workDir = workingDirectory ?? Environment.CurrentDirectory;
                    Logger.LogAction("SHELL_START_ATTEMPT", $"Starting shell in directory: {workDir}");
                    
                    _shellProcess = new Process
                    {
                        StartInfo = new ProcessStartInfo
                        {
                            FileName = "cmd.exe",
                            UseShellExecute = false,
                            RedirectStandardInput = true,
                            RedirectStandardOutput = true,
                            RedirectStandardError = true,
                            CreateNoWindow = true,
                            StandardOutputEncoding = Encoding.UTF8,
                            StandardErrorEncoding = Encoding.UTF8,
                            WorkingDirectory = workDir
                        }
                    };

                    _shellProcess.Start();
                    _shellInput = _shellProcess.StandardInput;

                    _outputReaderTask = Task.Run(() => ReadOutputAsync(_shellProcess.StandardOutput, _outputBuffer, _cancellationTokenSource.Token));
                    _errorReaderTask = Task.Run(() => ReadOutputAsync(_shellProcess.StandardError, _errorBuffer, _cancellationTokenSource.Token));

                    IsRunning = true;
                    Logger.LogAction("SHELL_STARTED", $"Shell process started successfully (PID: {_shellProcess.Id})");
                }
                catch (Exception ex)
                {
                    Logger.LogError($"Failed to start shell: {ex.Message}");
                    CleanupProcess();
                    throw;
                }
            }
        }

        public void SendInput(string input)
        {
            lock (_processLock)
            {
                if (!IsRunning || _shellInput == null)
                {
                    Logger.LogError("Shell input attempted but shell is not running");
                    throw new InvalidOperationException("Shell is not running");
                }

                try
                {
                    Logger.LogAction("SHELL_INPUT", $"Sending command: {input}");
                    _shellInput.WriteLine(input);
                    _shellInput.Flush();
                }
                catch (Exception ex)
                {
                    Logger.LogError($"Failed to send shell input: {ex.Message}");
                    StopShell();
                    throw;
                }
            }
        }

        public string GetOutput()
        {
            var output = new StringBuilder();
            while (_outputBuffer.TryDequeue(out string line))
            {
                output.AppendLine(line);
            }
            return output.ToString();
        }

        public string GetError()
        {
            var error = new StringBuilder();
            while (_errorBuffer.TryDequeue(out string line))
            {
                error.AppendLine(line);
            }
            return error.ToString();
        }

        public void StopShell()
        {
            lock (_processLock)
            {
                if (!IsRunning)
                {
                    Logger.LogWarning("Shell stop requested but shell is not running");
                    return;
                }

                Logger.LogAction("SHELL_STOP_ATTEMPT", "Stopping shell process");
                IsRunning = false;
                _cancellationTokenSource.Cancel();

                try
                {
                    _shellInput?.Close();
                    
                    if (_shellProcess != null && !_shellProcess.HasExited)
                    {
                        _shellProcess.Kill();
                        Logger.LogAction("SHELL_KILLED", $"Shell process terminated (PID: {_shellProcess.Id})");
                    }
                }
                catch (Exception ex)
                {
                    Logger.LogWarning($"Exception during shell cleanup: {ex.Message}");
                }

                CleanupProcess();
                Logger.LogAction("SHELL_STOPPED", "Shell stopped and resources cleaned up");
            }
        }

        private async Task ReadOutputAsync(StreamReader reader, ConcurrentQueue<string> buffer, CancellationToken cancellationToken)
        {
            try
            {
                char[] charBuffer = new char[1024];
                StringBuilder lineBuffer = new StringBuilder();
                
                while (!cancellationToken.IsCancellationRequested && !reader.EndOfStream)
                {
                    int charsRead = await reader.ReadAsync(charBuffer, 0, charBuffer.Length);
                    if (charsRead > 0)
                    {
                        for (int i = 0; i < charsRead; i++)
                        {
                            char c = charBuffer[i];
                            if (c == '\n')
                            {
                                // Complete line found, remove trailing \r if present
                                string line = lineBuffer.ToString();
                                if (line.EndsWith("\r"))
                                {
                                    line = line.Substring(0, line.Length - 1);
                                }
                                buffer.Enqueue(line);
                                lineBuffer.Clear();
                            }
                            else if (c != '\r')
                            {
                                // Add character to line buffer (skip \r as we handle it above)
                                lineBuffer.Append(c);
                            }
                        }
                        
                        // If we have partial content and no more data is immediately available,
                        // and the buffer is not empty, add it as a line to ensure output is not lost
                        if (lineBuffer.Length > 0 && reader.Peek() == -1)
                        {
                            buffer.Enqueue(lineBuffer.ToString());
                            lineBuffer.Clear();
                        }
                    }
                    else
                    {
                        // No more data available, but check if we have a partial line
                        if (lineBuffer.Length > 0)
                        {
                            buffer.Enqueue(lineBuffer.ToString());
                            lineBuffer.Clear();
                        }
                        // Small delay to prevent tight loop when no data is available
                        await Task.Delay(10, cancellationToken);
                    }
                }
                
                // Handle any remaining content in the buffer when the stream ends
                if (lineBuffer.Length > 0)
                {
                    buffer.Enqueue(lineBuffer.ToString());
                }
            }
            catch (Exception ex)
            {
                // Log the exception for debugging
                Logger.LogWarning($"ReadOutputAsync exception: {ex.Message}");
            }
        }

        private void CleanupProcess()
        {
            try
            {
                _shellInput?.Dispose();
                _shellProcess?.Dispose();
            }
            catch { }

            _shellInput = null;
            _shellProcess = null;
        }

        public void Dispose()
        {
            StopShell();
            _cancellationTokenSource?.Dispose();
        }
    }
}