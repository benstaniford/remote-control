using System;
using System.Windows.Forms;

namespace RemoteControlApp
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            using (var context = new TrayApplicationContext())
            {
                Application.Run(context);
            }
        }
    }
}