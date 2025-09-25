using System;
using System.Diagnostics;
using System.Drawing;
using System.Reflection;
using System.Windows.Forms;

namespace RemoteControlApp
{
    public partial class AboutForm : Form
    {
        public AboutForm()
        {
            InitializeComponent();
            LoadVersionInfo();
        }

        private void InitializeComponent()
        {
            this.SuspendLayout();
            
            // Form properties
            this.AutoScaleDimensions = new SizeF(6F, 13F);
            this.AutoScaleMode = AutoScaleMode.Font;
            this.ClientSize = new Size(400, 250);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.Text = "About Remote Control App";
            this.ShowIcon = false;
            this.ShowInTaskbar = false;

            // Title label
            var titleLabel = new Label()
            {
                Text = "Remote Control App",
                Font = new Font("Microsoft Sans Serif", 14F, FontStyle.Bold),
                Location = new Point(20, 20),
                Size = new Size(360, 30),
                TextAlign = ContentAlignment.MiddleCenter
            };
            this.Controls.Add(titleLabel);

            // Version label
            var versionLabel = new Label()
            {
                Name = "versionLabel",
                Text = "Version: Loading...",
                Font = new Font("Microsoft Sans Serif", 10F),
                Location = new Point(20, 60),
                Size = new Size(360, 20),
                TextAlign = ContentAlignment.MiddleCenter
            };
            this.Controls.Add(versionLabel);

            // Description label
            var descriptionLabel = new Label()
            {
                Text = "Remote browser control, shell access, and file transfer via HTTP JSON API.\nListens on localhost:8417",
                Font = new Font("Microsoft Sans Serif", 9F),
                Location = new Point(20, 90),
                Size = new Size(360, 40),
                TextAlign = ContentAlignment.MiddleCenter
            };
            this.Controls.Add(descriptionLabel);

            // Copyright label
            var copyrightLabel = new Label()
            {
                Text = "Copyright © 2025",
                Font = new Font("Microsoft Sans Serif", 9F),
                Location = new Point(20, 140),
                Size = new Size(360, 20),
                TextAlign = ContentAlignment.MiddleCenter
            };
            this.Controls.Add(copyrightLabel);

            // OK button
            var okButton = new Button()
            {
                Text = "OK",
                Location = new Point(162, 180),
                Size = new Size(75, 23),
                UseVisualStyleBackColor = true,
                DialogResult = DialogResult.OK
            };
            okButton.Click += (sender, e) => this.Close();
            this.Controls.Add(okButton);
            this.AcceptButton = okButton;

            this.ResumeLayout(false);
        }

        private void LoadVersionInfo()
        {
            try
            {
                string version = GetGitVersion();
                var versionLabel = this.Controls.Find("versionLabel", false)[0] as Label;
                if (versionLabel != null)
                {
                    versionLabel.Text = $"Version: {version}";
                }
            }
            catch
            {
                var versionLabel = this.Controls.Find("versionLabel", false)[0] as Label;
                if (versionLabel != null)
                {
                    versionLabel.Text = "Version: Unknown";
                }
            }
        }

        private string GetGitVersion()
        {
            var assembly = Assembly.GetExecutingAssembly();
            
            // Try to get the informational version first (contains git tag when built properly)
            var informationalVersion = assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion;
            if (!string.IsNullOrEmpty(informationalVersion) && informationalVersion != "1.0.0-dev")
            {
                return informationalVersion.StartsWith("v") ? informationalVersion : $"v{informationalVersion}";
            }

            // Fallback to assembly version
            var version = assembly.GetName().Version;
            return $"v{version.Major}.{version.Minor}.{version.Build}";
        }
    }
}