Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class CertStoreHelper {
    [DllImport("crypt32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern IntPtr CertOpenStore(string lpszStoreProvider, uint dwEncodingType, IntPtr hCryptProv, uint dwFlags, string pvPara);
    [DllImport("crypt32.dll", SetLastError = true)]
    public static extern bool CertAddEncodedCertificateToStore(IntPtr hCertStore, uint dwCertEncodingType, byte[] pbCertEncoded, uint cbCertEncoded, uint dwAddDisposition, out IntPtr ppCertContext);
    [DllImport("crypt32.dll", SetLastError = true)]
    public static extern bool CertCloseStore(IntPtr hCertStore, uint dwFlags);
    public static string Add(string path, bool machine) {
        var cert = new System.Security.Cryptography.X509Certificates.X509Certificate2(path);
        uint flags = machine ? 0x20000u : 0x10000u;   // LOCAL_MACHINE / CURRENT_USER
        IntPtr store = CertOpenStore("System", 0x10000u, IntPtr.Zero, flags, "Root");
        if (store == IntPtr.Zero) return "CertOpenStore failed: " + Marshal.GetLastWin32Error();
        IntPtr ctx;
        bool ok = CertAddEncodedCertificateToStore(store, 0x00010001u, cert.RawData, (uint)cert.RawData.Length, 3u, out ctx);
        int err = Marshal.GetLastWin32Error();
        CertCloseStore(store, 0);
        return ok ? "ADDED " + cert.Thumbprint : "CertAdd failed: " + err;
    }
}
"@
"user  : " + [CertStoreHelper]::Add('E:\Projects\NAS542\tls\root_ca.crt', $false)
"machine: " + [CertStoreHelper]::Add('E:\Projects\NAS542\tls\root_ca.crt', $true)
