<#
.SYNOPSIS
    Generates TLS/SSL Certificates for Rural Delivery Droid Fleet MQTT Broker and Node-RED.
.DESCRIPTION
    Creates Root CA, Broker Server Certificate (with SAN), and Client Certificates (mTLS)
    either using OpenSSL (if installed/found) or via native Windows PKI cmdlets.
    Outputs PEM format certificates (.crt) and RSA private keys (.key) ready for Mosquitto and Node-RED.
#>

[CmdletBinding()]
param (
    [string]$OutputDir = "",
    [string]$BrokerHost = "localhost",
    [string]$BrokerIP = "127.0.0.1",
    [int]$ValidityYears = 5
)

$ErrorActionPreference = "Stop"

if (-not $OutputDir) {
    if ($PSScriptRoot) {
        $OutputDir = Join-Path $PSScriptRoot "certs"
    } else {
        $OutputDir = Join-Path (Get-Location) "tls_mqtt_broker\certs"
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Rural Delivery Droid Fleet - TLS Certificate Generator   " -ForegroundColor Cyan
Write-Host " Output Directory: $OutputDir                             " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Compile native C# RSA PEM Exporter if not already present in session
if (-not ([System.Management.Automation.PSTypeName]'RsaPemExporter').Type) {
    Add-Type -TypeDefinition @"
using System;
using System.IO;
using System.Security.Cryptography;

public class RsaPemExporter {
    private static void WriteLength(BinaryWriter bw, int len) {
        if (len < 128) {
            bw.Write((byte)len);
        } else if (len <= 0xFF) {
            bw.Write((byte)0x81);
            bw.Write((byte)len);
        } else {
            bw.Write((byte)0x82);
            bw.Write((byte)(len >> 8));
            bw.Write((byte)(len & 0xFF));
        }
    }

    private static void WriteInteger(BinaryWriter bw, byte[] data) {
        bw.Write((byte)0x02);
        int prefixZero = (data.Length > 0 && (data[0] & 0x80) != 0) ? 1 : 0;
        WriteLength(bw, data.Length + prefixZero);
        if (prefixZero == 1) bw.Write((byte)0x00);
        bw.Write(data);
    }

    public static string ExportPkcs1PrivateKeyPem(RSAParameters p) {
        using (var mem = new MemoryStream()) {
            using (var bw = new BinaryWriter(mem)) {
                WriteInteger(bw, new byte[] { 0x00 }); // Version = 0
                WriteInteger(bw, p.Modulus);
                WriteInteger(bw, p.Exponent);
                WriteInteger(bw, p.D);
                WriteInteger(bw, p.P);
                WriteInteger(bw, p.Q);
                WriteInteger(bw, p.DP);
                WriteInteger(bw, p.DQ);
                WriteInteger(bw, p.InverseQ);
            }
            byte[] body = mem.ToArray();
            using (var outMem = new MemoryStream()) {
                using (var outBw = new BinaryWriter(outMem)) {
                    outBw.Write((byte)0x30); // SEQUENCE
                    WriteLength(outBw, body.Length);
                    outBw.Write(body);
                }
                string b64 = Convert.ToBase64String(outMem.ToArray(), Base64FormattingOptions.InsertLineBreaks);
                return "-----BEGIN RSA PRIVATE KEY-----\r\n" + b64 + "\r\n-----END RSA PRIVATE KEY-----\r\n";
            }
        }
    }
}
"@
}

# Check if OpenSSL is available in PATH or common Git directories
$opensslPath = $null
if (Get-Command openssl -ErrorAction SilentlyContinue) {
    $opensslPath = "openssl"
} elseif (Test-Path "C:\Program Files\Git\usr\bin\openssl.exe") {
    $opensslPath = "C:\Program Files\Git\usr\bin\openssl.exe"
}

if ($opensslPath) {
    Write-Host "[+] Found OpenSSL at: $opensslPath. Generating via OpenSSL..." -ForegroundColor Green
    Push-Location $OutputDir
    try {
        $cnfPath = Join-Path (Split-Path $OutputDir -Parent) "openssl.cnf"
        if (-not (Test-Path $cnfPath)) { $cnfPath = "openssl.cnf" }
        
        # 1. Root CA
        & $opensslPath genrsa -out ca.key 4096
        & $opensslPath req -new -x509 -days 3650 -key ca.key -out ca.crt -config $cnfPath -extensions v3_ca -subj "/C=US/ST=Rural/L=Hub/O=Rural Droid Logistics/OU=Security/CN=Rural-Delivery-Fleet-CA"
        
        # 2. Broker Server
        & $opensslPath genrsa -out server.key 2048
        & $opensslPath req -new -key server.key -out server.csr -subj "/C=US/ST=Rural/L=Hub/O=Rural Droid Logistics/OU=Broker/CN=$BrokerHost"
        & $opensslPath x509 -req -days ($ValidityYears * 365) -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -extfile $cnfPath -extensions server_cert
        
        # 3. Droid Client (mTLS)
        & $opensslPath genrsa -out droid01.key 2048
        & $opensslPath req -new -key droid01.key -out droid01.csr -subj "/C=US/ST=Rural/L=Hub/O=Rural Droid Logistics/OU=Droids/CN=droid-alpha-01"
        & $opensslPath x509 -req -days ($ValidityYears * 365) -in droid01.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out droid01.crt -extfile $cnfPath -extensions client_cert

        # 4. Node-RED Client (mTLS)
        & $opensslPath genrsa -out nodered.key 2048
        & $opensslPath req -new -key nodered.key -out nodered.csr -subj "/C=US/ST=Rural/L=Hub/O=Rural Droid Logistics/OU=Dispatch/CN=nodered-central-dispatch"
        & $opensslPath x509 -req -days ($ValidityYears * 365) -in nodered.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out nodered.crt -extfile $cnfPath -extensions client_cert

        Write-Host "[OK] All certificates successfully generated using OpenSSL!" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "[!] OpenSSL binary not detected. Using native Windows PKI module..." -ForegroundColor Yellow
    
    # 1. Create Root CA
    Write-Host "[1/4] Generating Root CA (ca.crt and ca.key)..." -ForegroundColor Cyan
    $caCert = New-SelfSignedCertificate `
        -Subject "CN=Rural-Delivery-Fleet-CA, O=Rural Droid Logistics, OU=Security" `
        -KeyUsage CertSign, CRLSign, DigitalSignature `
        -KeyLength 4096 `
        -KeyExportPolicy Exportable `
        -NotAfter (Get-Date).AddYears($ValidityYears) `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -FriendlyName "Rural Droid Fleet Root CA"

    $caBytes = $caCert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
    $caBase64 = [System.Convert]::ToBase64String($caBytes, [System.Base64FormattingOptions]::InsertLineBreaks)
    [System.IO.File]::WriteAllText("$OutputDir\ca.crt", "-----BEGIN CERTIFICATE-----`r`n$caBase64`r`n-----END CERTIFICATE-----`r`n")
    
    $caRsa = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($caCert)
    $caKeyPem = [RsaPemExporter]::ExportPkcs1PrivateKeyPem($caRsa.ExportParameters($true))
    [System.IO.File]::WriteAllText("$OutputDir\ca.key", $caKeyPem)

    # 2. Create Broker Server Cert signed by Root CA
    Write-Host "[2/4] Generating MQTT Server Certificate (server.crt and server.key)..." -ForegroundColor Cyan
    $sanList = @("localhost", "mqtt.ruraldelivery.local", "broker.deliverydroid.lan", $BrokerHost, $BrokerIP)
    $serverCert = New-SelfSignedCertificate `
        -Signer $caCert `
        -Subject "CN=$BrokerHost, O=Rural Droid Logistics, OU=Broker" `
        -DnsName $sanList `
        -KeyUsage DigitalSignature, KeyEncipherment `
        -Type SSLServerAuthentication `
        -KeyLength 2048 `
        -KeyExportPolicy Exportable `
        -NotAfter (Get-Date).AddYears($ValidityYears) `
        -CertStoreLocation "Cert:\CurrentUser\My"

    $serverBytes = $serverCert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
    $serverBase64 = [System.Convert]::ToBase64String($serverBytes, [System.Base64FormattingOptions]::InsertLineBreaks)
    [System.IO.File]::WriteAllText("$OutputDir\server.crt", "-----BEGIN CERTIFICATE-----`r`n$serverBase64`r`n-----END CERTIFICATE-----`r`n")

    $serverRsa = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($serverCert)
    $serverKeyPem = [RsaPemExporter]::ExportPkcs1PrivateKeyPem($serverRsa.ExportParameters($true))
    [System.IO.File]::WriteAllText("$OutputDir\server.key", $serverKeyPem)

    # 3. Create Droid Client Cert signed by Root CA
    Write-Host "[3/4] Generating Droid Client Certificate (droid01.crt and droid01.key)..." -ForegroundColor Cyan
    $droidCert = New-SelfSignedCertificate `
        -Signer $caCert `
        -Subject "CN=droid-alpha-01, O=Rural Droid Logistics, OU=Droids" `
        -KeyUsage DigitalSignature, KeyEncipherment `
        -Type Custom `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.2") `
        -KeyLength 2048 `
        -KeyExportPolicy Exportable `
        -NotAfter (Get-Date).AddYears($ValidityYears) `
        -CertStoreLocation "Cert:\CurrentUser\My"

    $droidBytes = $droidCert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
    $droidBase64 = [System.Convert]::ToBase64String($droidBytes, [System.Base64FormattingOptions]::InsertLineBreaks)
    [System.IO.File]::WriteAllText("$OutputDir\droid01.crt", "-----BEGIN CERTIFICATE-----`r`n$droidBase64`r`n-----END CERTIFICATE-----`r`n")

    $droidRsa = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($droidCert)
    $droidKeyPem = [RsaPemExporter]::ExportPkcs1PrivateKeyPem($droidRsa.ExportParameters($true))
    [System.IO.File]::WriteAllText("$OutputDir\droid01.key", $droidKeyPem)

    # 4. Create Node-RED Dispatch Client Cert
    Write-Host "[4/4] Generating Node-RED Client Certificate (nodered.crt and nodered.key)..." -ForegroundColor Cyan
    $nrCert = New-SelfSignedCertificate `
        -Signer $caCert `
        -Subject "CN=nodered-central-dispatch, O=Rural Droid Logistics, OU=Dispatch" `
        -KeyUsage DigitalSignature, KeyEncipherment `
        -Type Custom `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.2") `
        -KeyLength 2048 `
        -KeyExportPolicy Exportable `
        -NotAfter (Get-Date).AddYears($ValidityYears) `
        -CertStoreLocation "Cert:\CurrentUser\My"

    $nrBytes = $nrCert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
    $nrBase64 = [System.Convert]::ToBase64String($nrBytes, [System.Base64FormattingOptions]::InsertLineBreaks)
    [System.IO.File]::WriteAllText("$OutputDir\nodered.crt", "-----BEGIN CERTIFICATE-----`r`n$nrBase64`r`n-----END CERTIFICATE-----`r`n")

    $nrRsa = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($nrCert)
    $nrKeyPem = [RsaPemExporter]::ExportPkcs1PrivateKeyPem($nrRsa.ExportParameters($true))
    [System.IO.File]::WriteAllText("$OutputDir\nodered.key", $nrKeyPem)

    # Clean up Windows Cert store entries
    Remove-Item ("Cert:\CurrentUser\My\" + $caCert.Thumbprint) -Force
    Remove-Item ("Cert:\CurrentUser\My\" + $serverCert.Thumbprint) -Force
    Remove-Item ("Cert:\CurrentUser\My\" + $droidCert.Thumbprint) -Force
    Remove-Item ("Cert:\CurrentUser\My\" + $nrCert.Thumbprint) -Force

    Write-Host "[OK] All PEM certificates and RSA private keys generated in: $OutputDir" -ForegroundColor Green
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Certificate Generation Complete!                         " -ForegroundColor Green
Write-Host " Files created:                                           " -ForegroundColor Green
Write-Host "   ca.crt, ca.key           (Root Certificate Authority)  " -ForegroundColor White
Write-Host "   server.crt, server.key   (Mosquitto Broker Server)     " -ForegroundColor White
Write-Host "   droid01.crt, droid01.key (Droid mTLS Client)           " -ForegroundColor White
Write-Host "   nodered.crt, nodered.key (Node-RED Dispatch Console)   " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
