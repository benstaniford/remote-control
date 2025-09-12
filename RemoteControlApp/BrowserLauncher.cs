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
                if (!Uri.IsWellFormedUriString(url, UriKind.Absolute))
                {
                    throw new ArgumentException("Invalid URL format");
                }

                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = url,
                    UseShellExecute = true
                };

                Process.Start(psi);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Failed to launch browser: {ex.Message}", ex);
            }
        }
    }
}