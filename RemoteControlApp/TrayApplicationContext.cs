using System;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

namespace RemoteControlApp
{
    public class TrayApplicationContext : ApplicationContext, IDisposable
    {
        private NotifyIcon _trayIcon;
        private HttpServer _httpServer;

        public TrayApplicationContext()
        {
            InitializeTray();
            StartServer();
        }

        private void InitializeTray()
        {
            _trayIcon = new NotifyIcon()
            {
                Icon = GetIcon(),
                ContextMenuStrip = new ContextMenuStrip(),
                Visible = true,
                Text = "Remote Control App - Listening on localhost:417"
            };

            _trayIcon.ContextMenuStrip.Items.Add("Show Status", null, ShowStatus);
            _trayIcon.ContextMenuStrip.Items.Add("-");
            _trayIcon.ContextMenuStrip.Items.Add("Exit", null, Exit);

            _trayIcon.DoubleClick += ShowStatus;
        }

        private Icon GetIcon()
        {
            try
            {
                var assembly = Assembly.GetExecutingAssembly();
                var stream = assembly.GetManifestResourceStream("RemoteControlApp.app.ico");
                if (stream != null)
                {
                    return new Icon(stream);
                }
            }
            catch { }

            return SystemIcons.Application;
        }

        private void StartServer()
        {
            try
            {
                _httpServer = new HttpServer();
                _httpServer.Start();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to start HTTP server: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                ExitThread();
            }
        }

        private void ShowStatus(object sender, EventArgs e)
        {
            MessageBox.Show("Remote Control App is running and listening on localhost:417\n\nJSON Protocol:\n{\n  \"action\": \"launch_browser\",\n  \"url\": \"https://example.com\"\n}", 
                           "Status", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void Exit(object sender, EventArgs e)
        {
            _trayIcon.Visible = false;
            ExitThread();
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                _httpServer?.Dispose();
                _trayIcon?.Dispose();
            }
            base.Dispose(disposing);
        }

        public new void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }
    }
}