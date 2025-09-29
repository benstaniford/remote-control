using System;
using System.Diagnostics;

namespace RemoteControlApp
{
    public static class BrowserLauncher
    {
        public static void LaunchUrl(string url)
        {
            try
            {
                Logger.LogAction("BROWSER_LAUNCH_ATTEMPT", $"Attempting to launch URL: {url}");
                
                if (!Uri.IsWellFormedUriString(url, UriKind.Absolute))
                {
                    Logger.LogError($"Invalid URL format: {url}");
                    throw new ArgumentException("Invalid URL format");
                }

                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = url,
                    UseShellExecute = true
                };

                Process.Start(psi);
                Logger.LogAction("BROWSER_LAUNCHED", $"Successfully launched URL: {url}");
            }
            catch (Exception ex)
            {
                Logger.LogError($"Failed to launch browser for URL {url}: {ex.Message}");
                throw new InvalidOperationException($"Failed to launch browser: {ex.Message}", ex);
            }
        }
    }
}