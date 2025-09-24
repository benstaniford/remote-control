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

        public void StartShell()
        {
            lock (_processLock)
            {
                if (IsRunning)
                    return;

                try
                {
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
                            StandardErrorEncoding = Encoding.UTF8
                        }
                    };

                    _shellProcess.Start();
                    _shellInput = _shellProcess.StandardInput;

                    _outputReaderTask = Task.Run(() => ReadOutputAsync(_shellProcess.StandardOutput, _outputBuffer, _cancellationTokenSource.Token));
                    _errorReaderTask = Task.Run(() => ReadOutputAsync(_shellProcess.StandardError, _errorBuffer, _cancellationTokenSource.Token));

                    IsRunning = true;
                }
                catch (Exception)
                {
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
                    throw new InvalidOperationException("Shell is not running");

                try
                {
                    _shellInput.WriteLine(input);
                    _shellInput.Flush();
                }
                catch (Exception)
                {
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
                    return;

                IsRunning = false;
                _cancellationTokenSource.Cancel();

                try
                {
                    _shellInput?.Close();
                    
                    if (_shellProcess != null && !_shellProcess.HasExited)
                    {
                        _shellProcess.Kill();
                    }
                }
                catch { }

                CleanupProcess();
            }
        }

        private async Task ReadOutputAsync(StreamReader reader, ConcurrentQueue<string> buffer, CancellationToken cancellationToken)
        {
            try
            {
                while (!cancellationToken.IsCancellationRequested && !reader.EndOfStream)
                {
                    string line = await reader.ReadLineAsync();
                    if (line != null)
                    {
                        buffer.Enqueue(line);
                    }
                }
            }
            catch (Exception)
            {
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