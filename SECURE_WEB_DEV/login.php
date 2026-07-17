<?php
session_start();
require_once("connexion.php");

$msg = "";
if ($_SERVER["REQUEST_METHOD"] == "POST") {
	$log = $_POST['login'] ?? "";
	$mdp = $_POST['mdp'] ?? "";
	$ville = $_POST['ville'] ?? "";
	
	if (!empty($log) && !empty($mdp)) {
		$sql = "SELECT id_user, login, mdp, statut, role FROM utilisateur WHERE login = :login AND mdp = :mdp AND est_actif = 1";
		$stmt = $mysqlConnection->prepare($sql);
		$stmt->execute([':login' => $log, ':mdp' => $mdp]);
		$user = $stmt->fetch(PDO::FETCH_ASSOC);
		
		if ($user) {
			$_SESSION['id_user'] = $user['id_user'];
			$_SESSION['login'] = $user['login'];
			$_SESSION['statut'] = $user['statut'];
			$_SESSION['role'] = $user['role'];
			setcookie("ville", $ville, time() + 3600, "/");
			
			header("Location: " . ($user['role'] === 'admin' ? 'admin_dashboard.php' : 'afficher_evenements.php'));
			exit();
		} else { $msg = "Identifiants incorrects."; }
	}
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Connexion</title>
<link rel="stylesheet" href="pfm.css">
</head>
<body>
<?php include("menu.php"); ?>
<div style="max-width: 600px; margin: 30px auto; background: white; padding: 25px; border-radius: 8px;">
<h2>Connexion utilisateur</h2>
<?php if(!empty($msg)) echo "<p style='color:red;'>$msg</p>"; ?>
<form method="POST" action="login.php">
Login : <br><input type="text" name="login" required><br><br>
Mot de passe : <br><input type="password" name="mdp" required><br><br>
Ville : <br>
<select name="ville" required>
<option value="Rabat">Rabat</option>
<option value="Casa">Casa</option>
<option value="Tanger">Tanger</option>
</select><br><br>
<button type="submit">Se connecter</button>
</form>
</div>
</body>
</html>
