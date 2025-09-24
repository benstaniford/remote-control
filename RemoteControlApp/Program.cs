using System;
using System.Threading;
using System.Windows.Forms;

namespace RemoteControlApp
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            // Check for detached mode argument
            bool detached = args.Length > 0 && (args[0] == "--detached" || args[0] == "-d");

            if (detached)
            {
                // Run in detached mode - start in separate thread and return immediately
                var thread = new Thread(() =>
                {
                    using (var context = new TrayApplicationContext())
                    {
                        Application.Run(context);
                    }
                })
                {
                    IsBackground = false,
                    ApartmentState = ApartmentState.STA
                };

                thread.Start();
                Console.WriteLine("Remote Control App started in background. Tray icon should be visible.");
            }
            else
            {
                // Default blocking mode
                using (var context = new TrayApplicationContext())
                {
                    Application.Run(context);
                }
            }
        }
    }
}