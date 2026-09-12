$Users = Import-Csv -Path ".\users.csv"
foreach ($u in $Users) {
    $OUPath = "OU=$($u.Service),OU=CORP-FR,DC=corp,DC=lab,DC=local"
    New-ADUser -Name "$($u.Prenom) $($u.Nom)" `
        -GivenName $u.Prenom -Surname $u.Nom `
        -SamAccountName $u.Login -UserPrincipalName "$($u.Login)@corp.lab.local" `
        -Path $OUPath -AccountPassword (ConvertTo-SecureString "P@ssw0rd2026!" -AsPlainText -Force) `
        -Enabled $true -ChangePasswordAtLogon $true
    Write-Host "Créé : $($u.Login) dans $OUPath"
}
