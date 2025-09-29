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
        private CancellationTokenSource _cancellationTokenSource;
        private Task _outputReaderTask;
        private Task _errorReaderTask;
        private readonly object _processLock = new object();

        public bool IsRunning 
        { 
            get 
            {
                lock (_processLock)
                {
                    // Check if we think it's running but the process has actually died
                    if (_isRunning && _shellProcess != null && _shellProcess.HasExited)
                    {
                        Logger.LogError($"Shell process has died unexpectedly (exit code: {_shellProcess.ExitCode})");
                        CleanupProcess();
                        _isRunning = false;
                    }
                    return _isRunning;
                }
            }
            private set { _isRunning = value; }
        }
        
        private bool _isRunning;
        private string _lastWorkingDirectory;

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
                if (_isRunning)
                {
                    Logger.LogWarning("Shell start requested but shell is already running");
                    return;
                }

                try
                {
                    // Create a new cancellation token source for this shell session
                    _cancellationTokenSource?.Dispose();
                    _cancellationTokenSource = new CancellationTokenSource();
                    
                    var workDir = workingDirectory ?? Environment.CurrentDirectory;
                    _lastWorkingDirectory = workDir;
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

                    Logger.LogAction("SHELL_READERS_STARTING", "Starting output and error reader tasks");
                    _outputReaderTask = Task.Run(() => ReadOutputAsync(_shellProcess.StandardOutput, _outputBuffer, _cancellationTokenSource.Token));
                    _errorReaderTask = Task.Run(() => ReadOutputAsync(_shellProcess.StandardError, _errorBuffer, _cancellationTokenSource.Token));

                    _isRunning = true;
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
                // Check if shell is actually running (this will detect dead processes)
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
            // Check process health first
            var isHealthy = IsRunning;
            var readerTasksHealthy = AreReaderTasksHealthy();
            
            var output = new StringBuilder();
            int lineCount = 0;
            while (_outputBuffer.TryDequeue(out string line))
            {
                output.AppendLine(line);
                lineCount++;
            }
            
            var result = output.ToString();
            Logger.LogAction("SHELL_OUTPUT_RETRIEVED", $"Retrieved {lineCount} lines, {result.Length} characters, Shell healthy: {isHealthy}, Readers healthy: {readerTasksHealthy}");
            
            // If no output but readers are dead, try to restart them
            if (lineCount == 0 && isHealthy && !readerTasksHealthy)
            {
                Logger.LogWarning("No output retrieved but shell is healthy and readers are dead - attempting to restart readers");
                TryRestartReaderTasks();
            }
            
            return result;
        }

        public string GetError()
        {
            var error = new StringBuilder();
            int lineCount = 0;
            while (_errorBuffer.TryDequeue(out string line))
            {
                error.AppendLine(line);
                lineCount++;
            }
            
            var result = error.ToString();
            if (lineCount > 0)
            {
                Logger.LogAction("SHELL_ERROR_RETRIEVED", $"Retrieved {lineCount} error lines, {result.Length} characters");
            }
            return result;
        }

        public void StopShell()
        {
            lock (_processLock)
            {
                if (!_isRunning)
                {
                    Logger.LogWarning("Shell stop requested but shell is not running");
                    return;
                }

                Logger.LogAction("SHELL_STOP_ATTEMPT", "Stopping shell process");
                _isRunning = false;
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
            var readerType = buffer == _outputBuffer ? "OUTPUT" : "ERROR";
            Logger.LogAction($"SHELL_{readerType}_READER_STARTED", $"Reader task started, cancellation requested: {cancellationToken.IsCancellationRequested}");
            
            try
            {
                char[] charBuffer = new char[1024];
                StringBuilder lineBuffer = new StringBuilder();
                int linesRead = 0;
                
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
                                linesRead++;
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
                            linesRead++;
                            lineBuffer.Clear();
                        }
                    }
                    else
                    {
                        // No more data available, but check if we have a partial line
                        if (lineBuffer.Length > 0)
                        {
                            buffer.Enqueue(lineBuffer.ToString());
                            linesRead++;
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
                    linesRead++;
                }
                
                Logger.LogAction($"SHELL_{readerType}_READER_FINISHED", $"Reader task finished, lines read: {linesRead}, cancellation: {cancellationToken.IsCancellationRequested}");
            }
            catch (Exception ex)
            {
                Logger.LogError($"SHELL_{readerType}_READER_ERROR: Reader task failed: {ex.Message}");
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

        private bool AreReaderTasksHealthy()
        {
            try
            {
                var outputTaskHealthy = _outputReaderTask != null && 
                                       !_outputReaderTask.IsCompleted && 
                                       !_outputReaderTask.IsCanceled && 
                                       !_outputReaderTask.IsFaulted;
                                       
                var errorTaskHealthy = _errorReaderTask != null && 
                                      !_errorReaderTask.IsCompleted && 
                                      !_errorReaderTask.IsCanceled && 
                                      !_errorReaderTask.IsFaulted;
                                      
                return outputTaskHealthy && errorTaskHealthy;
            }
            catch
            {
                return false;
            }
        }
        
        private void TryRestartReaderTasks()
        {
            lock (_processLock)
            {
                if (!_isRunning || _shellProcess == null || _shellProcess.HasExited)
                {
                    Logger.LogWarning("Cannot restart reader tasks - shell process is not running");
                    return;
                }

                try
                {
                    Logger.LogAction("SHELL_READERS_RESTART", "Restarting reader tasks");
                    
                    // Start new reader tasks (the old ones should have exited)
                    _outputReaderTask = Task.Run(() => ReadOutputAsync(_shellProcess.StandardOutput, _outputBuffer, _cancellationTokenSource.Token));
                    _errorReaderTask = Task.Run(() => ReadOutputAsync(_shellProcess.StandardError, _errorBuffer, _cancellationTokenSource.Token));
                    
                    Logger.LogAction("SHELL_READERS_RESTARTED", "Reader tasks restarted successfully");
                }
                catch (Exception ex)
                {
                    Logger.LogError($"Failed to restart reader tasks: {ex.Message}");
                }
            }
        }

        public bool TryAutoRestart()
        {
            lock (_processLock)
            {
                if (_isRunning)
                {
                    Logger.LogWarning("Auto-restart requested but shell is still running");
                    return true;
                }

                try
                {
                    Logger.LogAction("SHELL_AUTO_RESTART", $"Attempting to restart shell in directory: {_lastWorkingDirectory ?? Environment.CurrentDirectory}");
                    StartShell(_lastWorkingDirectory);
                    return true;
                }
                catch (Exception ex)
                {
                    Logger.LogError($"Auto-restart failed: {ex.Message}");
                    return false;
                }
            }
        }

        public void Dispose()
        {
            StopShell();
            _cancellationTokenSource?.Dispose();
        }
    }
}