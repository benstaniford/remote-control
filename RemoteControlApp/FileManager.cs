using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace RemoteControlApp
{
    public class FileManager
    {
        private const int MaxFileSize = 100 * 1024 * 1024; // 100MB limit
        private const int BufferSize = 64 * 1024; // 64KB buffer

        public string ReadFileAsBase64(string filePath)
        {
            if (string.IsNullOrWhiteSpace(filePath))
                throw new ArgumentException("File path cannot be empty");

            if (!File.Exists(filePath))
                throw new FileNotFoundException($"File not found: {filePath}");

            var fileInfo = new FileInfo(filePath);
            if (fileInfo.Length > MaxFileSize)
                throw new InvalidOperationException($"File too large. Maximum size is {MaxFileSize / (1024 * 1024)}MB");

            try
            {
                byte[] fileBytes = File.ReadAllBytes(filePath);
                return Convert.ToBase64String(fileBytes);
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to file: {filePath}");
            }
            catch (IOException ex)
            {
                throw new IOException($"Error reading file: {ex.Message}", ex);
            }
        }

        public void WriteFileFromBase64(string filePath, string base64Content)
        {
            if (string.IsNullOrWhiteSpace(filePath))
                throw new ArgumentException("File path cannot be empty");

            if (string.IsNullOrWhiteSpace(base64Content))
                throw new ArgumentException("File content cannot be empty");

            try
            {
                byte[] fileBytes = Convert.FromBase64String(base64Content);
                
                if (fileBytes.Length > MaxFileSize)
                    throw new InvalidOperationException($"File too large. Maximum size is {MaxFileSize / (1024 * 1024)}MB");

                // Ensure directory exists
                string directory = Path.GetDirectoryName(filePath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                File.WriteAllBytes(filePath, fileBytes);
            }
            catch (FormatException)
            {
                throw new FormatException("Invalid base64 content");
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to file: {filePath}");
            }
            catch (IOException ex)
            {
                throw new IOException($"Error writing file: {ex.Message}", ex);
            }
        }

        public FileInfo GetFileInfo(string filePath)
        {
            if (string.IsNullOrWhiteSpace(filePath))
                throw new ArgumentException("File path cannot be empty");

            if (!File.Exists(filePath))
                throw new FileNotFoundException($"File not found: {filePath}");

            try
            {
                return new FileInfo(filePath);
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to file: {filePath}");
            }
        }

        public bool FileExists(string filePath)
        {
            if (string.IsNullOrWhiteSpace(filePath))
                return false;

            try
            {
                return File.Exists(filePath);
            }
            catch
            {
                return false;
            }
        }

        public string GetFileHash(string filePath)
        {
            if (!File.Exists(filePath))
                throw new FileNotFoundException($"File not found: {filePath}");

            try
            {
                using (var sha256 = SHA256.Create())
                using (var stream = File.OpenRead(filePath))
                {
                    byte[] hash = sha256.ComputeHash(stream);
                    return Convert.ToBase64String(hash);
                }
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to file: {filePath}");
            }
            catch (IOException ex)
            {
                throw new IOException($"Error reading file for hash: {ex.Message}", ex);
            }
        }

        public void DeleteFile(string filePath)
        {
            if (string.IsNullOrWhiteSpace(filePath))
                throw new ArgumentException("File path cannot be empty");

            if (!File.Exists(filePath))
                throw new FileNotFoundException($"File not found: {filePath}");

            try
            {
                File.Delete(filePath);
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to file: {filePath}");
            }
            catch (IOException ex)
            {
                throw new IOException($"Error deleting file: {ex.Message}", ex);
            }
        }

        public string[] ListFiles(string directoryPath, string pattern = "*")
        {
            if (string.IsNullOrWhiteSpace(directoryPath))
                throw new ArgumentException("Directory path cannot be empty");

            if (!Directory.Exists(directoryPath))
                throw new DirectoryNotFoundException($"Directory not found: {directoryPath}");

            try
            {
                return Directory.GetFiles(directoryPath, pattern);
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to directory: {directoryPath}");
            }
            catch (IOException ex)
            {
                throw new IOException($"Error listing files: {ex.Message}", ex);
            }
        }
    }
}