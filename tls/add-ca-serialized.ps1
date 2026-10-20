Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class CertReg {
    [DllImport("crypt32.dll", SetLastError = true)]
    public static extern IntPtr CertCreateCertificateContext(uint enc, byte[] data, uint len);
    [DllImport("crypt32.dll", SetLastError = true)]
    public static extern bool CertSerializeCertificateStoreElement(IntPtr ctx, uint flags, byte[] buf, ref uint size);
    [DllImport("crypt32.dll")]
    public static extern bool CertFreeCertificateContext(IntPtr ctx);

    public static byte[] Serialize(byte[] der) {
        IntPtr ctx = CertCreateCertificateContext(0x00010001u, der, (uint)der.Length);
        if (ctx == IntPtr.Zero) throw new Exception("CertCreateCertificateContext failed: " + Marshal.GetLastWin32Error());
        uint size = 0;
        CertSerializeCertificateStoreElement(ctx, 0, null, ref size);
        if (size == 0) throw new Exception("size query failed: " + Marshal.GetLastWin32Error());
        byte[] buf = new byte[size];
        if (!CertSerializeCertificateStoreElement(ctx, 0, buf, ref size))
            throw new Exception("serialize failed: " + Marshal.GetLastWin32Error());
        CertFreeCertificateContext(ctx);
        Array.Resize(ref buf, (int)size);
        return buf;
    }
}
"@

$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2('E:\Projects\NAS542\tls\root_ca.crt')
$blob = [CertReg]::Serialize($cert.RawData)
"der len : $($cert.RawData.Length)"
"blob len: $($blob.Length)"
"head    : " + (($blob[0..11] | ForEach-Object { $_.ToString('X2') }) -join ' ')

$path = "HKCU:\Software\Microsoft\SystemCertificates\Root\Certificates\$($cert.Thumbprint)"
New-Item -Path $path -Force | Out-Null
New-ItemProperty -Path $path -Name Blob -PropertyType Binary -Value $blob -Force | Out-Null
"written : $path"
