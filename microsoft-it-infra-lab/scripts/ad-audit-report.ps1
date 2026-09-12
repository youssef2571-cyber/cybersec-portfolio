$InactiveDays = 90
$Threshold = (Get-Date).AddDays(-$InactiveDays)

$InactiveUsers = Get-ADUser -Filter {LastLogonTimestamp -lt $Threshold -and Enabled -eq $true} -Properties LastLogonTimestamp | Select-Object Name, SamAccountName, @{N="DerniereConnexion";E={[DateTime]::FromFileTime($_.LastLogonTimestamp)}}

$InactiveUsers | Export-Csv -Path "C:\Rapports\rapport-comptes-inactifs.csv" -NoTypeInformation -Encoding UTF8
Write-Host "$($InactiveUsers.Count) comptes inactifs depuis plus de $InactiveDays jours détectés."
