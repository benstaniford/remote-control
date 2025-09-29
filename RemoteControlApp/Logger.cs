using System;
using System.IO;

namespace RemoteControlApp
{
    public static class Logger
    {
        private static readonly string LogDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RemoteControlApp");
        private static readonly string LogFilePath = Path.Combine(LogDirectory, "RemoteControl.log");
        private static readonly object _lockObject = new object();

        static Logger()
        {
            InitializeLogFile();
        }

        private static void InitializeLogFile()
        {
            try
            {
                if (!Directory.Exists(LogDirectory))
                {
                    Directory.CreateDirectory(LogDirectory);
                }

                File.WriteAllText(LogFilePath, $"Remote Control App Log - Started at {DateTime.Now:yyyy-MM-dd HH:mm:ss}\n");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to initialize log file: {ex.Message}");
            }
        }

        public static void LogInfo(string message)
        {
            WriteLog("INFO", message);
        }

        public static void LogError(string message)
        {
            WriteLog("ERROR", message);
        }

        public static void LogWarning(string message)
        {
            WriteLog("WARNING", message);
        }

        public static void LogRequest(string method, string action, string details = null)
        {
            var logMessage = $"HTTP {method} - Action: {action}";
            if (!string.IsNullOrEmpty(details))
            {
                logMessage += $" - {details}";
            }
            WriteLog("REQUEST", logMessage);
        }

        public static void LogAction(string action, string details = null)
        {
            var logMessage = action;
            if (!string.IsNullOrEmpty(details))
            {
                logMessage += $" - {details}";
            }
            WriteLog("ACTION", logMessage);
        }

        private static void WriteLog(string level, string message)
        {
            try
            {
                lock (_lockObject)
                {
                    var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
                    var logEntry = $"[{timestamp}] [{level}] {message}\n";
                    File.AppendAllText(LogFilePath, logEntry);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to write to log: {ex.Message}");
            }
        }

        public static string GetLogFilePath()
        {
            return LogFilePath;
        }

        public static void OpenLogFile()
        {
            try
            {
                if (File.Exists(LogFilePath))
                {
                    System.Diagnostics.Process.Start("notepad.exe", LogFilePath);
                }
                else
                {
                    System.Windows.Forms.MessageBox.Show("Log file not found.", "Error", 
                        System.Windows.Forms.MessageBoxButtons.OK, System.Windows.Forms.MessageBoxIcon.Warning);
                }
            }
            catch (Exception ex)
            {
                System.Windows.Forms.MessageBox.Show($"Failed to open log file: {ex.Message}", "Error", 
                    System.Windows.Forms.MessageBoxButtons.OK, System.Windows.Forms.MessageBoxIcon.Error);
            }
        }
    }
}