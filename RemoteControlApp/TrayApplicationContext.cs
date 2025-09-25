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
        private ShellManager _shellManager;
        private FileManager _fileManager;

        public TrayApplicationContext()
        {
            InitializeTray();
            _shellManager = new ShellManager();
            _fileManager = new FileManager();
            StartServer();
        }

        private void InitializeTray()
        {
            _trayIcon = new NotifyIcon()
            {
                Icon = GetIcon(),
                ContextMenuStrip = new ContextMenuStrip(),
                Visible = true,
                Text = "Remote Control App - Listening on localhost:8417"
            };

            _trayIcon.ContextMenuStrip.Items.Add("Show Status", null, ShowStatus);
            _trayIcon.ContextMenuStrip.Items.Add("About", null, ShowAbout);
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
                _httpServer = new HttpServer(_shellManager, _fileManager);
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
            var shellStatus = _shellManager.IsRunning ? "Running" : "Stopped";
            MessageBox.Show($"Remote Control App is running and listening on localhost:8417\n\nShell Status: {shellStatus}\n\nJSON Protocol:\n{{\n  \"action\": \"launch_browser\",\n  \"url\": \"https://example.com\"\n}}\n\nShell Actions:\n- shell_start, shell_stop, shell_status\n- shell_input, shell_output", 
                           "Status", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void ShowAbout(object sender, EventArgs e)
        {
            using (var aboutForm = new AboutForm())
            {
                aboutForm.ShowDialog();
            }
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
                _shellManager?.Dispose();
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