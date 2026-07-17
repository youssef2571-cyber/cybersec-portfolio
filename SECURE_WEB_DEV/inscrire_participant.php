<?php

require_once("connexion.php");

$erreur = [];

if ($_SERVER["REQUEST_METHOD"] == "POST") {
	$nom = $_POST['nom'] ?? "";
	$prenom = $_POST['prenom'] ?? "";
	$email = $_POST['email'] ?? "";
	$login = $_POST['login'] ?? "";
	$mdp = $_POST['mdp'] ?? "";
	$statut = $_POST['statut'] ?? "";
	$code = $_POST['code_etudiant'] ?? "";
	$interets = $_POST['interets'] ?? []; 
	$motivation = $_POST['motivation'] ?? "Néant";

	if (empty($nom) || empty($prenom) || empty($email) || empty($login) || empty($mdp) || empty($statut)) {
		$erreur[] = "Veuillez remplir les champs obligatoires.";
	}
	

	if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
		$erreur[] = "Format d'email invalide.";
	} else {
		$res = explode("@", $email);
		if (!isset($res[1]) || $res[1] !== "um5r.ac.ma") {
			$erreur[] = "L'email doit appartenir au domaine @um5r.ac.ma.";
		}
	}
	
	
	if (count($interets) < 2) { 
		$erreur[] = "Cochez au moins deux centres d'intérêt."; 
	}
	
	$fichier_nom = null;
	
	if (isset($_FILES['justificatif']) && $_FILES['justificatif']['error'] == 0) {
		$fichier_nom = $_FILES['justificatif']['name'];
		$ext = pathinfo($fichier_nom, PATHINFO_EXTENSION);
		
		if (!in_array($ext, ['pdf', 'jpg', 'jpeg', 'png'])) { 
			$erreur[] = "Format de fichier invalide."; 
		}
		
		if ($_FILES['justificatif']['size'] > 2 * 1024 * 1024) { 
			$erreur[] = "Fichier trop volumineux (> 2 Mo)."; 
		}
		
		if (empty($erreur)) {
			$dossier = "uploads/";
			$tmp = $_FILES['justificatif']['tmp_name'];
			
			move_uploaded_file($tmp, $dossier . $fichier_nom);
		}
		
	} else { 
		$erreur[] = "Justificatif obligatoire."; 
	}
	if (empty($erreur)) {
		try {
			$sql = "INSERT INTO utilisateur (nom, prenom, email, login, mdp, statut, code_etudiant, motivation, Justificatif, est_actif, role) 
			VALUES (:n, :p, :e, :l, :m, :s, :c, :mot, :j, 1, 'user')";
			$stmt = $mysqlConnection->prepare($sql);
			$stmt->execute([
				':n' => $nom, ':p' => $prenom, ':e' => $email, ':l' => $login,
				':m' => $mdp, ':s' => $statut, ':c' => !empty($code) ? $code : null,
						   ':mot' => $motivation, ':j' => $fichier_nom
			]);
			$success = true;
		} catch (PDOException $e) { 
			$erreur[] = "Erreur SQL (Identifiant ou email déjà utilisé) : " . $e->getMessage(); 
		}
	}
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Traitement Inscription</title>
<link rel="stylesheet" href="pfm.css">
</head>
<body>
<?php include("menu.php"); ?>
<div style="max-width: 600px; margin: 30px auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
<?php
if (isset($success) && $success) {
	echo "<h3 style='color:green;'>✔️ Compte créé avec succès !</h3>";
	echo "<a href='login.php'><button style='padding:10px 15px; background:#3498db; color:white; border:none; cursor:pointer; font-weight:bold;'>connexion</button></a>";
} else if (!empty($erreur)) {
	echo "<h3 style='color:#e74c3c;'>Erreurs rencontrées :</h3>";
	foreach ($erreur as $err) { 
		echo "<p style='color:#c0392b;'>- " . htmlspecialchars($err) . "</p>"; 
	}
	echo "<br><a href='inscription.html' style='color:#3498db; font-weight:bold; text-decoration:none;'>⬅ Retour au formulaire</a>";
} else {
	echo "<p>Aucune donnée reçue. Veuillez utiliser le formulaire d'inscription.</p>";
	echo "<a href='inscription.html'>Aller à l'inscription</a>";
}
?>
</div>
</body>
</html>
