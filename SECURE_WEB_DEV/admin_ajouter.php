<?php
session_start();
require_once("connexion.php");
if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'admin') { header("Location: login.php"); exit(); }

if ($_SERVER["REQUEST_METHOD"] == "POST") {
	try {
		$sql = "INSERT INTO event (titre, description, date_event, lieu, prix_etudiant, prix_public, places_disponibles) VALUES (:t, :d, :dt, :l, :pe, :pp, :pl)";
		$stmt = $mysqlConnection->prepare($sql);
		$stmt->execute([':t' => $_POST['titre'], ':d' => $_POST['description'], ':dt' => $_POST['date_event'], ':l' => $_POST['lieu'], ':pe' => $_POST['prix_etudiant'], ':pp' => $_POST['prix_public'], ':pl' => $_POST['places_disponibles']]);
		header("Location: admin_dashboard.php"); exit();
	} catch (PDOException $e) { echo "<p style='color:red;'>Erreur : " . $e->getMessage() . "</p>"; }
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"><title>Ajouter</title><link rel="stylesheet" href="pfm.css">
</head>
<body>
<?php include("menu.php"); ?>
<div style="max-width: 700px; margin: 30px auto; background: white; padding: 25px;">
<h2>Ajouter un événement</h2>
<form method="POST" action="admin_ajouter.php">
Titre : <input type="text" name="titre" required><br><br>
Description : <br><textarea name="description" rows="3" style="width:100%;"></textarea><br><br>
Date : <input type="date" name="date_event" required><br><br>
Lieu : <input type="text" name="lieu" required><br><br>
Prix Étudiant (DH) : <input type="number" step="0.01" name="prix_etudiant" required><br><br>
Prix Public (DH) : <input type="number" step="0.01" name="prix_public" required><br><br>
Places disponibles : <input type="number" name="places_disponibles" required><br><br>
<button type="submit">Enregistrer</button> <a href="admin_dashboard.php" style="margin-left:15px;">Annuler</a>
</form>
</div>
</body>
</html>
